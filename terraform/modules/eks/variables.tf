# modules/eks/variables.tf
# Input variables for EKS module

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
}

variable "cluster_version" {
  description = "Kubernetes version for the EKS cluster"
  type        = string
  default     = "1.33"
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where EKS cluster will be created"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for EKS cluster"
  type        = list(string)
}

variable "node_groups" {
  description = "Configuration for EKS managed node groups"
  type = map(object({
    desired_size   = number
    min_size       = number
    max_size       = number
    instance_types = list(string)
    labels         = map(string)
    taints = list(object({
      key    = string
      value  = string
      effect = string
    }))
  }))
  default = {
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
}

variable "openai_secret_arn" {
  description = "ARN of the OpenAI API key secret"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
