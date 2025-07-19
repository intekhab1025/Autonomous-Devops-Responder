# modules/applications/variables.tf
# Input variables for applications module

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace for applications"
  type        = string
  default     = "default"
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

variable "openai_secret_arn" {
  description = "ARN of the OpenAI API key secret"
  type        = string
}

variable "service_account_name" {
  description = "Name of the Kubernetes service account"
  type        = string
  default     = "incident-responder-sa"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
