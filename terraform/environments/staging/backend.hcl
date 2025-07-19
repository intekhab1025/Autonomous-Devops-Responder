# Backend configuration for staging environment
# terraform/environments/staging/backend.hcl

bucket         = "incident-responder-terraform-state-staging"
key            = "incident-responder/staging/terraform.tfstate"
region         = "us-west-2"
encrypt        = true
dynamodb_table = "incident-responder-terraform-locks"
