# main.tf - Modular architecture using custom modules
############################################################
# Production-ready EKS infrastructure with modular design
############################################################

# Networking Module
module "networking" {
  source = "./modules/networking"

  environment          = var.environment
  name_prefix          = local.name_prefix
  cluster_name         = local.cluster_name
  vpc_cidr             = "10.0.0.0/16"
  private_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnet_cidrs  = ["10.0.101.0/24", "10.0.102.0/24"]
  common_tags          = local.common_tags
}

# Secrets Module
module "secrets" {
  source = "./modules/secrets"

  name_prefix    = local.name_prefix
  openai_api_key = var.openai_api_key
  common_tags    = local.common_tags
}

# EKS Module
module "eks" {
  source = "./modules/eks"

  cluster_name      = local.cluster_name
  cluster_version   = "1.33"
  environment       = var.environment
  vpc_id            = module.networking.vpc_id
  subnet_ids        = module.networking.private_subnet_ids
  openai_secret_arn = module.secrets.openai_api_key_secret_arn
  common_tags       = local.common_tags

  node_groups = {
    system = {
      desired_size   = 2
      min_size       = 1
      max_size       = 3
      instance_types = ["t3.medium"]
      labels = {
        nodegroup = "system"
        workload  = "system"
      }
      taints = []
    }
    prometheus = {
      desired_size   = 1
      min_size       = 1
      max_size       = 3
      instance_types = ["t3.medium"]
      labels = {
        nodegroup = "prometheus"
        workload  = "prometheus"
      }
      taints = [{
        key    = "workload"
        value  = "prometheus"
        effect = "NO_SCHEDULE"
      }]
    }
  }

  depends_on = [module.networking, module.secrets]
}

# AWS Load Balancer Controller Module
module "aws_load_balancer_controller" {
  source = "./modules/aws-load-balancer-controller"

  cluster_name      = local.cluster_name
  oidc_provider_arn = module.eks.oidc_provider_arn
  oidc_provider     = module.eks.oidc_provider
  vpc_id            = module.networking.vpc_id
  aws_region        = var.aws_region
  name_prefix       = local.name_prefix
  common_tags       = local.common_tags

  # Explicit dependencies for proper teardown order
  depends_on = [
    module.eks,
    module.networking
  ]
}

# Monitoring Module
module "monitoring" {
  source = "./modules/monitoring"

  name_prefix                           = local.name_prefix
  namespace                             = "monitoring"
  grafana_admin_password                = var.grafana_admin_password
  vpc_id                                = module.networking.vpc_id
  aws_load_balancer_controller_role_arn = module.aws_load_balancer_controller.iam_role_arn
  common_tags                           = local.common_tags

  # Explicit dependencies for proper teardown order
  depends_on = [
    module.eks,
    module.aws_load_balancer_controller,
    module.networking
  ]
}

# Applications Module
module "applications" {
  source = "./modules/applications"

  name_prefix              = local.name_prefix
  namespace                = "default"
  incident_responder_image = var.incident_responder_image
  openai_secret_arn        = module.secrets.openai_api_key_secret_arn
  common_tags              = local.common_tags

  # Explicit dependencies for proper teardown order
  depends_on = [
    module.eks,
    module.aws_load_balancer_controller,
    module.networking,
    module.secrets
  ]
}
