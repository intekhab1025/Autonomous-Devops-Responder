# modules/monitoring/variables.tf
# Input variables for monitoring module

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace for monitoring components"
  type        = string
  default     = "monitoring"
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  sensitive   = true
}

variable "vpc_id" {
  description = "VPC ID for ALB"
  type        = string
}

variable "aws_load_balancer_controller_role_arn" {
  description = "ARN of the AWS Load Balancer Controller IAM role"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
