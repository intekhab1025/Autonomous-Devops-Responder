terraform {
  required_version = ">= 1.5.0"

  # Remote backend configuration - configure per environment
  backend "s3" {
    # Configure these in backend.hcl files per environment
    # bucket         = "incident-responder-terraform-state-${var.environment}"
    # key            = "incident-responder/terraform.tfstate"
    # region         = "us-west-2"
    # encrypt        = true
    # dynamodb_table = "incident-responder-terraform-locks"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.31"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.24"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
