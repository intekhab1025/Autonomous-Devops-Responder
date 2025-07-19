# modules/secrets/variables.tf
# Input variables for secrets module

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "openai_api_key" {
  description = "OpenAI/OpenRouter API key"
  type        = string
  sensitive   = true
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
