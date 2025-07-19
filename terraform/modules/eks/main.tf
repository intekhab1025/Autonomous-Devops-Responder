# modules/eks/main.tf
# EKS cluster and managed node groups

# EKS Module
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "20.37.1"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  cluster_endpoint_public_access = true

  vpc_id     = var.vpc_id
  subnet_ids = var.subnet_ids

  # Transform node groups to match expected format
  eks_managed_node_groups = {
    for name, config in var.node_groups : name => {
      desired_size   = config.desired_size
      min_size       = config.min_size
      max_size       = config.max_size
      instance_types = config.instance_types

      labels = merge(config.labels, {
        environment = var.environment
      })

      taints = config.taints

      # Only add additional policies, let EKS module handle the standard ones
      iam_role_additional_policies = {
        AmazonEBSCSIDriverPolicy = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
      }

      # Don't create duplicate attachments for default policies
      iam_role_attach_cni_policy = false
    }
  }

  cluster_addons = {
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  enable_cluster_creator_admin_permissions = true
  tags                                     = var.common_tags
}

# IAM policy for node groups to access secrets
data "aws_iam_policy_document" "eks_nodes_secretsmanager" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = [var.openai_secret_arn]
  }
}

resource "aws_iam_role_policy" "eks_nodes_secretsmanager" {
  name   = "${var.cluster_name}-nodes-secretsmanager"
  role   = module.eks.eks_managed_node_groups["system"]["iam_role_name"]
  policy = data.aws_iam_policy_document.eks_nodes_secretsmanager.json
}
