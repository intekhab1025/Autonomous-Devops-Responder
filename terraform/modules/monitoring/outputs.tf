# modules/monitoring/outputs.tf
# Output values from monitoring module

output "monitoring_namespace" {
  description = "Name of the monitoring namespace"
  value       = kubernetes_namespace.monitoring.metadata[0].name
}

output "namespace" {
  description = "Kubernetes namespace for monitoring resources"
  value       = kubernetes_namespace.monitoring.metadata[0].name
}

output "prometheus_release_name" {
  description = "Name of the Prometheus Helm release"
  value       = helm_release.prometheus.name
}

output "grafana_release_name" {
  description = "Name of the Grafana Helm release"
  value       = helm_release.grafana.name
}

output "grafana_url" {
  description = "URL for Grafana dashboard"
  value       = try("http://${kubernetes_ingress_v1.grafana_alb.status[0].load_balancer[0].ingress[0].hostname}", "Pending...")
}

output "grafana_admin_user" {
  description = "Grafana admin username"
  value       = "admin"
}

output "prometheus_service_name" {
  description = "Prometheus service name"
  value       = "prometheus-kube-prometheus-prometheus"
}

output "grafana_service_name" {
  description = "Grafana service name"
  value       = "grafana"
}
