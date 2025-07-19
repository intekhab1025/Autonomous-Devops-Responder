
provider "aws" {
  region = var.aws_region
}

# Kubernetes and Helm providers will be configured after EKS cluster is created
# These use the exec plugin for authentication, which is more reliable than tokens
provider "kubernetes" {
  host                   = try(module.eks.cluster_endpoint, "")
  cluster_ca_certificate = try(base64decode(module.eks.cluster_certificate_authority_data), "")
  
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args = [
      "eks",
      "get-token",
      "--cluster-name",
      try(module.eks.cluster_name, local.cluster_name),
      "--region",
      var.aws_region,
      "--output",
      "json"
    ]
  }
}

provider "helm" {
  kubernetes {
    host                   = try(module.eks.cluster_endpoint, "")
    cluster_ca_certificate = try(base64decode(module.eks.cluster_certificate_authority_data), "")
    
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args = [
        "eks",
        "get-token",
        "--cluster-name",
        try(module.eks.cluster_name, local.cluster_name),
        "--region",
        var.aws_region,
        "--output",
        "json"
      ]
    }
  }
}



