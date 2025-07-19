# Backend configuration for production environment
# terraform/environments/prod/backend.hcl

bucket         = "incident-responder-terraform-state-prod"
key            = "incident-responder/prod/terraform.tfstate"
region         = "us-west-2"
encrypt        = true
dynamodb_table = "incident-responder-terraform-locks"
