# Root module outputs - aggregated from submodules
############################################################

# Networking Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.networking.vpc_cidr_block
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = module.networking.private_subnet_ids
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.networking.public_subnet_ids
}

# EKS Outputs
output "cluster_endpoint" {
  description = "EKS cluster API server endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_security_group_id" {
  description = "Security group ID for the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "cluster_oidc_issuer_url" {
  description = "OIDC issuer URL for the EKS cluster"
  value       = module.eks.oidc_provider
}

output "node_groups" {
  description = "EKS node group information"
  value       = module.eks.node_groups
  sensitive   = true
}

# ALB Controller Outputs
output "aws_load_balancer_controller_role_arn" {
  description = "ARN of the AWS Load Balancer Controller IAM role"
  value       = module.aws_load_balancer_controller.iam_role_arn
}

# Secrets Outputs
output "openai_secret_arn" {
  description = "ARN of the OpenAI API key secret"
  value       = module.secrets.openai_api_key_secret_arn
  sensitive   = true
}

# Application URLs
output "incident_responder_alb_url" {
  description = "ALB URL for the incident-responder app"
  value       = module.applications.incident_responder_url
}

output "grafana_alb_url" {
  description = "ALB URL for Grafana"
  value       = module.monitoring.grafana_url
}

# Monitoring Outputs
output "monitoring_namespace" {
  description = "Kubernetes namespace for monitoring"
  value       = module.monitoring.namespace
}

# Quick Start Commands
output "kubectl_config_command" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

output "cluster_status_check" {
  description = "Command to check cluster status"
  value       = "kubectl get nodes"
}

# Summary
output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    vpc_id           = module.networking.vpc_id
    cluster_name     = module.eks.cluster_name
    cluster_endpoint = module.eks.cluster_endpoint
    apps = {
      incident_responder = module.applications.incident_responder_url
      grafana           = module.monitoring.grafana_url
    }
    kubectl_command = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
  }
}


