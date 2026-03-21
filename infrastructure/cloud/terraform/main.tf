terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
  required_version = ">= 1.2.0"
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

module "networking" {
  source = "./networking.tf"
}

module "monitoring" {
  source = "./monitoring.tf"
}

module "scaling" {
  source = "./scaling.tf"
}

module "security" {
  source = "./security.tf"
}

output "infrastructure_status" {
  value = "Terraform modules initialized and configured."
}
