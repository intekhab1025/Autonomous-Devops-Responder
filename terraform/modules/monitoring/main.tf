# modules/monitoring/main.tf
# Monitoring infrastructure with Prometheus and Grafana

# Monitoring namespace
resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = var.namespace
    labels = {
      name        = var.namespace
      environment = "monitoring"
    }
  }
}

# Prometheus Helm Release
resource "helm_release" "prometheus" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "75.10.0" # Pin to specific version for stability

  create_namespace = false

  # Helm release lifecycle management
  force_update    = false
  cleanup_on_fail = true
  max_history     = 3

  set {
    name  = "grafana.adminPassword"
    value = var.grafana_admin_password
  }

  set {
    name  = "prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues"
    value = "false"
  }

  # Resource limits for production readiness
  set {
    name  = "prometheus.prometheusSpec.resources.requests.memory"
    value = "2Gi"
  }

  set {
    name  = "prometheus.prometheusSpec.resources.limits.memory"
    value = "4Gi"
  }

  # Storage configuration
  set {
    name  = "prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage"
    value = "50Gi"
  }

  values = [file("${path.root}/../helm/prometheus-values.yaml")]

  depends_on = [kubernetes_namespace.monitoring]
}

# Grafana Helm Release (separate from Prometheus for flexibility)
resource "helm_release" "grafana" {
  name       = "grafana"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "grafana"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "7.0.19" # Pin to specific version

  create_namespace = false

  # Helm release lifecycle management
  force_update    = false
  cleanup_on_fail = true
  max_history     = 3

  set {
    name  = "adminPassword"
    value = var.grafana_admin_password
  }

  # Service type for ALB integration
  set {
    name  = "service.type"
    value = "ClusterIP"
  }

  set {
    name  = "service.port"
    value = "80"
  }

  # Resource limits
  set {
    name  = "resources.requests.memory"
    value = "256Mi"
  }

  set {
    name  = "resources.limits.memory"
    value = "512Mi"
  }

  values = [file("${path.root}/../helm/grafana-values.yaml")]

  depends_on = [kubernetes_namespace.monitoring]
}

# ALB Ingress for Grafana
resource "kubernetes_ingress_v1" "grafana_alb" {
  metadata {
    name      = "grafana-ingress"
    namespace = var.namespace
    annotations = {
      "alb.ingress.kubernetes.io/scheme"       = "internet-facing"
      "alb.ingress.kubernetes.io/target-type"  = "ip"
      "alb.ingress.kubernetes.io/listen-ports" = "[{\"HTTP\": 80}]"
      "alb.ingress.kubernetes.io/tags"         = join(",", [for k, v in var.common_tags : "${k}=${v}"])
    }
  }

  spec {
    ingress_class_name = "alb"
    rule {
      http {
        path {
          path      = "/"
          path_type = "Prefix"
          backend {
            service {
              name = "grafana"
              port {
                number = 80
              }
            }
          }
        }
      }
    }
  }

  depends_on = [helm_release.grafana]
}

# PrometheusRule for test applications
resource "kubernetes_manifest" "test_app_alerts" {
  manifest = {
    apiVersion = "monitoring.coreos.com/v1"
    kind       = "PrometheusRule"
    metadata = {
      name      = "test-app-alerts"
      namespace = var.namespace
      labels = {
        app                     = "kube-prometheus-stack"
        "app.kubernetes.io/name" = "kube-prometheus-stack"
        "app.kubernetes.io/part-of" = "kube-prometheus-stack"
        release                 = "prometheus"
      }
    }
    spec = {
      groups = [
        {
          name = "test-app.rules"
          rules = [
            {
              alert = "TestAppPodDown"
              expr  = "kube_deployment_status_replicas_available{deployment=\"test-app\"} < 1"
              for   = "1m"
              labels = {
                severity   = "critical"
                deployment = "test-app"
              }
              annotations = {
                summary     = "test-app deployment has no available pods."
                description = "The test-app deployment in the default namespace has no available pods."
              }
            },
            {
              alert = "TestAppHighMemoryUsage"
              expr  = "(container_memory_usage_bytes{pod=~\"test-app.*\",container!=\"POD\"} / container_spec_memory_limit_bytes{pod=~\"test-app.*\",container!=\"POD\"}) > 0.8"
              for   = "1m"
              labels = {
                severity   = "critical"
                deployment = "test-app"
              }
              annotations = {
                summary     = "Test app memory usage is above 80%"
                description = "Memory usage is above 80% for more than 1 minute in test-app."
              }
            },
            {
              alert = "TestApp2PodDown"
              expr  = "kube_deployment_status_replicas_available{deployment=\"test-app-2\"} < 3"
              for   = "1m"
              labels = {
                severity   = "critical"
                deployment = "test-app-2"
              }
              annotations = {
                summary     = "test-app-2 deployment has less than 3 available pods."
                description = "The test-app-2 deployment in the default namespace has less than 3 available pods."
              }
            },
            {
              alert = "TestApp2HighMemoryUsage"
              expr  = "(container_memory_usage_bytes{pod=~\"test-app-2.*\",container!=\"POD\"} / container_spec_memory_limit_bytes{pod=~\"test-app-2.*\",container!=\"POD\"}) > 0.8"
              for   = "1m"
              labels = {
                severity   = "critical"
                deployment = "test-app-2"
              }
              annotations = {
                summary     = "Test app 2 memory usage is above 80%"
                description = "Memory usage is above 80% for more than 1 minute in test-app-2."
              }
            }
          ]
        }
      ]
    }
  }

  depends_on = [helm_release.prometheus]
}
