# modules/applications/main.tf
# Application deployments and services

# Service Account for incident responder
resource "kubernetes_service_account" "incident_responder" {
  metadata {
    name      = var.service_account_name
    namespace = var.namespace
    labels = {
      app = "incident-responder"
    }
  }
}

# RBAC Role for incident responder
resource "kubernetes_role" "incident_responder_patch_deploy" {
  metadata {
    name      = "incident-responder-patch-deploy"
    namespace = var.namespace
  }

  rule {
    api_groups = ["apps"]
    resources  = ["deployments"]
    verbs      = ["get", "patch", "list"]
  }

  rule {
    api_groups = [""]
    resources  = ["pods"]
    verbs      = ["get", "list"]
  }
}

# RBAC Role Binding
resource "kubernetes_role_binding" "incident_responder_patch_deploy" {
  metadata {
    name      = "incident-responder-patch-deploy-binding"
    namespace = var.namespace
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.incident_responder_patch_deploy.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.incident_responder.metadata[0].name
    namespace = var.namespace
  }
}

# Incident Responder Deployment
resource "kubernetes_deployment" "incident_responder" {
  metadata {
    name      = "incident-responder"
    namespace = var.namespace
    labels = {
      app       = "incident-responder"
      component = "ai-agent"
      version   = "v1"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "incident-responder"
      }
    }

    template {
      metadata {
        labels = {
          app       = "incident-responder"
          component = "ai-agent"
          version   = "v1"
        }
      }

      spec {
        service_account_name = kubernetes_service_account.incident_responder.metadata[0].name

        container {
          name  = "incident-responder"
          image = var.incident_responder_image

          port {
            container_port = 8501
            name           = "http"
          }

          env {
            name  = "OPENROUTER_API_KEY_SECRET_ARN"
            value = var.openai_secret_arn
          }

          # Resource limits for production
          resources {
            requests = {
              memory = "256Mi"
              cpu    = "100m"
            }
            limits = {
              memory = "512Mi"
              cpu    = "500m"
            }
          }

          # Health checks
          liveness_probe {
            http_get {
              path = "/_stcore/health"
              port = 8501
            }
            initial_delay_seconds = 30
            period_seconds        = 10
            timeout_seconds       = 5
            failure_threshold     = 3
          }

          readiness_probe {
            http_get {
              path = "/_stcore/health"
              port = 8501
            }
            initial_delay_seconds = 5
            period_seconds        = 5
            timeout_seconds       = 3
            failure_threshold     = 3
          }
        }
      }
    }
  }
}

# Incident Responder Service
resource "kubernetes_service" "incident_responder" {
  metadata {
    name      = "incident-responder"
    namespace = var.namespace
    labels = {
      app = "incident-responder"
    }
  }

  spec {
    selector = {
      app = "incident-responder"
    }

    port {
      name        = "http"
      port        = 8501
      target_port = 8501
      protocol    = "TCP"
    }

    type = "ClusterIP"
  }
}

# ALB Ingress for Incident Responder
resource "kubernetes_ingress_v1" "incident_responder_alb" {
  metadata {
    name      = "incident-responder-ingress"
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
              name = kubernetes_service.incident_responder.metadata[0].name
              port {
                number = 8501
              }
            }
          }
        }
      }
    }
  }
}

# Test Applications for demonstration
resource "kubernetes_deployment" "test_app" {
  metadata {
    name      = "test-app"
    namespace = var.namespace
    labels = {
      app       = "test-app"
      component = "demo"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "test-app"
      }
    }

    template {
      metadata {
        labels = {
          app       = "test-app"
          component = "demo"
        }
      }

      spec {
        container {
          name  = "test-app"
          image = "busybox"
          args  = ["/bin/sh", "-c", "head -c 200000000 /dev/zero | tail > /dev/null; sleep 60"]

          port {
            container_port = 8080
          }

          resources {
            requests = {
              memory = "128Mi"
              cpu    = "100m"
            }
            limits = {
              memory = "256Mi"
              cpu    = "500m"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "test_app" {
  metadata {
    name      = "test-app"
    namespace = var.namespace
    labels = {
      app = "test-app"
    }
  }

  spec {
    selector = {
      app = "test-app"
    }

    port {
      port        = 8080
      target_port = 8080
    }

    type = "ClusterIP"
  }
}

# Test App 2
resource "kubernetes_deployment" "test_app_2" {
  metadata {
    name      = "test-app-2"
    namespace = var.namespace
    labels = {
      app       = "test-app-2"
      component = "demo"
    }
  }

  spec {
    replicas = 2

    selector {
      match_labels = {
        app = "test-app-2"
      }
    }

    template {
      metadata {
        labels = {
          app = "test-app-2"
        }
      }

      spec {
        container {
          name  = "test-app-2"
          image = "busybox"
          args  = ["/bin/sh", "-c", "while true; do echo hello; sleep 10; done"]

          port {
            container_port = 8080
          }

          resources {
            requests = {
              memory = "128Mi"
              cpu    = "100m"
            }
            limits = {
              memory = "256Mi"
              cpu    = "500m"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "test_app_2" {
  metadata {
    name      = "test-app-2"
    namespace = var.namespace
    labels = {
      app = "test-app-2"
    }
  }

  spec {
    selector = {
      app = "test-app-2"
    }

    port {
      port        = 8080
      target_port = 8080
    }

    type = "ClusterIP"
  }
}
