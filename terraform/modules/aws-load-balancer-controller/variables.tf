# modules/aws-load-balancer-controller/variables.tf
# Input variables for AWS Load Balancer Controller module

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
}

variable "oidc_provider_arn" {
  description = "ARN of the OIDC Provider for the EKS cluster"
  type        = string
}

variable "oidc_provider" {
  description = "The OpenID Connect identity provider (without https://)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where the load balancers will be created"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
