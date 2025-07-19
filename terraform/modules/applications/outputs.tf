# modules/applications/outputs.tf
# Output values from applications module

output "incident_responder_url" {
  description = "URL for the incident-responder application"
  value       = try("http://${kubernetes_ingress_v1.incident_responder_alb.status[0].load_balancer[0].ingress[0].hostname}", "Pending...")
}

output "incident_responder_service_name" {
  description = "Name of the incident responder service"
  value       = kubernetes_service.incident_responder.metadata[0].name
}

output "service_account_name" {
  description = "Name of the incident responder service account"
  value       = kubernetes_service_account.incident_responder.metadata[0].name
}

output "test_app_service_name" {
  description = "Name of the test app service"
  value       = kubernetes_service.test_app.metadata[0].name
}

output "test_app_2_service_name" {
  description = "Name of the test app 2 service"
  value       = kubernetes_service.test_app_2.metadata[0].name
}

output "deployments" {
  description = "List of deployment names"
  value = [
    kubernetes_deployment.incident_responder.metadata[0].name,
    kubernetes_deployment.test_app.metadata[0].name,
    kubernetes_deployment.test_app_2.metadata[0].name
  ]
}
