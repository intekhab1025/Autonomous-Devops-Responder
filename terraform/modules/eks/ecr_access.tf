# Custom IAM policy for enhanced ECR access
# This provides more specific permissions than the default AmazonEC2ContainerRegistryReadOnly policy

data "aws_iam_policy_document" "ecr_enhanced_access" {
  statement {
    effect = "Allow"
    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetAuthorizationToken",
      "ecr:DescribeRepositories",
      "ecr:ListImages",
      "ecr:DescribeImages"
    ]
    resources = ["*"]  # For specific repositories, use: ["arn:aws:ecr:${var.aws_region}:${data.aws_caller_identity.current.account_id}:repository/*"]
  }
  
  # GetAuthorizationToken needs to be allowed at account level
  statement {
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "ecr_enhanced_access" {
  name        = "${var.cluster_name}-ecr-enhanced-access"
  description = "Enhanced ECR access for EKS nodes to pull container images"
  policy      = data.aws_iam_policy_document.ecr_enhanced_access.json
  
  tags = var.common_tags
}

# Attach the policy to all node groups
resource "aws_iam_role_policy_attachment" "node_groups_ecr_enhanced_access" {
  for_each = tomap({
    for key, group in module.eks.eks_managed_node_groups : key => group.iam_role_name
  })

  policy_arn = aws_iam_policy.ecr_enhanced_access.arn
  role       = each.value
}

# Get current account ID
data "aws_caller_identity" "current" {}
