# Define reusable and configurable variables for Terraform infrastructure

# AWS region
variable "aws_region" {
  description = "The AWS region where resources will be deployed."
  type        = string
  default     = "us-east-1"
}

# AWS CLI profile
variable "aws_profile" {
  description = "AWS CLI profile to use for authentication."
  type        = string
  default     = "default"
}

# AMI ID for EC2 instances
variable "ami_id" {
  description = "AMI ID for EC2 instances."
  type        = string
  default     = "ami-0abcdef1234567890" # Replace with the appropriate AMI ID
}

# EC2 instance type
variable "instance_type" {
  description = "Type of EC2 instance to use for deployment."
  type        = string
  default     = "t2.micro"
}

# Key pair for SSH access
variable "key_pair_name" {
  description = "AWS key pair name for SSH access."
  type        = string
  default     = "trading-bot-key"
}

# VPC CIDR block
variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

# Public subnet CIDR block
variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet."
  type        = string
  default     = "10.0.1.0/24"
}

# Private subnet CIDR block
variable "private_subnet_cidr" {
  description = "CIDR block for the private subnet."
  type        = string
  default     = "10.0.2.0/24"
}

# Scaling configuration
variable "desired_capacity" {
  description = "Desired number of instances in the auto-scaling group."
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of instances in the auto-scaling group."
  type        = number
  default     = 3
}

variable "min_capacity" {
  description = "Minimum number of instances in the auto-scaling group."
  type        = number
  default     = 1
}

# Docker image for the trading bot
variable "docker_image" {
  description = "Docker image for the trading bot."
  type        = string
  default     = "myrepo/trading-bot:latest"
}

# Security configuration
variable "allowed_ip" {
  description = "IP address range allowed for SSH access."
  type        = string
  default     = "0.0.0.0/0" # Update for production use
}

# Monitoring toggle
variable "enable_monitoring" {
  description = "Enable or disable monitoring with Prometheus and Grafana."
  type        = bool
  default     = true
}
