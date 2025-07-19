# Local values for computed and derived configurations
# terraform/locals.tf

locals {
  # Naming convention with environment prefix
  name_prefix = var.environment

  # Auto-generate cluster name if not provided
  cluster_name = var.cluster_name != "" ? var.cluster_name : "${var.environment}-incident-responder-eks"

  # Common tags applied to all resources
  common_tags = merge(var.common_tags, {
    Environment = var.environment
    ManagedBy   = "terraform"
    Project     = "incident-responder"
  })
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}
