# Terraform provider configuration

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
  # AWS region and profile for authentication
  region  = var.aws_region
  profile = var.aws_profile
}

# Optional: Add other cloud providers if needed
# provider "google" {
#   project = var.google_project_id
#   region  = var.google_region
# }
