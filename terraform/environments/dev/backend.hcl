# Backend configuration for development environment
# terraform/environments/dev/backend.hcl

bucket         = "incident-responder-terraform-state-dev"
key            = "incident-responder/dev/terraform.tfstate"
region         = "us-west-2"
encrypt        = true
dynamodb_table = "incident-responder-terraform-locks"
