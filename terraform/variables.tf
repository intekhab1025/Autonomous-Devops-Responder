# Production-ready variables with proper validation and documentation

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-west-2"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "AWS region must be a valid region format (e.g., us-west-2)."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "cluster_name" {
  description = "EKS cluster name (auto-generated if not provided)"
  type        = string
  default     = ""
}

variable "openai_api_key" {
  description = "OpenAI/OpenRouter API key to store in AWS Secrets Manager"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.openai_api_key) > 0
    error_message = "OpenAI API key cannot be empty."
  }
}

variable "grafana_admin_password" {
  description = "Grafana admin password (minimum 12 characters)"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.grafana_admin_password) >= 12
    error_message = "Grafana admin password must be at least 12 characters."
  }
}

variable "prometheus_admin_password" {
  description = "Prometheus admin password (minimum 12 characters)"
  type        = string
  default     = ""
  sensitive   = true

  validation {
    condition     = var.prometheus_admin_password == "" || length(var.prometheus_admin_password) >= 12
    error_message = "Prometheus admin password must be at least 12 characters if provided."
  }
}

variable "incident_responder_image" {
  description = "Docker image for incident responder application"
  type        = string
  default     = ""

  validation {
    condition     = var.incident_responder_image != "" && can(regex("^([a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?(/[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?)*)(:[a-zA-Z0-9._-]+)?$", var.incident_responder_image))
    error_message = "Image must be provided and be a valid Docker image format (e.g., <account-id>.dkr.ecr.<region>.amazonaws.com/incident-responder:latest)."
  }
}

# Common tags
variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project   = "incident-responder"
    ManagedBy = "terraform"
  }
}
