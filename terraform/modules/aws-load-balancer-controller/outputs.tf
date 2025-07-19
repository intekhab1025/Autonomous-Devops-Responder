# modules/aws-load-balancer-controller/outputs.tf
# Output values from AWS Load Balancer Controller module

output "iam_role_arn" {
  description = "ARN of the AWS Load Balancer Controller IAM role"
  value       = aws_iam_role.alb_controller.arn
}

output "iam_role_name" {
  description = "Name of the AWS Load Balancer Controller IAM role"
  value       = aws_iam_role.alb_controller.name
}

output "iam_policy_arn" {
  description = "ARN of the AWS Load Balancer Controller IAM policy"
  value       = aws_iam_policy.alb_controller_policy.arn
}

output "helm_release_name" {
  description = "Name of the AWS Load Balancer Controller Helm release"
  value       = helm_release.aws_load_balancer_controller.name
}

output "service_account_name" {
  description = "Name of the AWS Load Balancer Controller service account"
  value       = "aws-load-balancer-controller"
}
