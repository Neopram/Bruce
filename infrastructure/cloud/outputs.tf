# Outputs for Terraform infrastructure deployment

# VPC ID
output "vpc_id" {
  description = "The ID of the created VPC."
  value       = aws_vpc.trading_bot_vpc.id
}

# Public Subnet ID
output "public_subnet_id" {
  description = "The ID of the public subnet."
  value       = aws_subnet.public_subnet.id
}

# Private Subnet ID
output "private_subnet_id" {
  description = "The ID of the private subnet."
  value       = aws_subnet.private_subnet.id
}

# Internet Gateway ID
output "internet_gateway_id" {
  description = "The ID of the Internet Gateway."
  value       = aws_internet_gateway.internet_gateway.id
}

# NAT Gateway Public IP
output "nat_gateway_public_ip" {
  description = "The public IP of the NAT Gateway."
  value       = aws_eip.nat_eip.public_ip
}

# NAT Gateway ID
output "nat_gateway_id" {
  description = "The ID of the NAT Gateway."
  value       = aws_nat_gateway.nat_gateway.id
}

# Public Route Table ID
output "public_route_table_id" {
  description = "The ID of the public route table."
  value       = aws_route_table.public_route_table.id
}

# Private Route Table ID
output "private_route_table_id" {
  description = "The ID of the private route table."
  value       = aws_route_table.private_route_table.id
}

# Auto-scaling Group Name
output "autoscaling_group_name" {
  description = "The name of the auto-scaling group."
  value       = aws_autoscaling_group.trading_bot_asg.name
}

# Prometheus Public IP
output "prometheus_public_ip" {
  description = "Public IP address of the Prometheus instance."
  value       = aws_instance.prometheus.public_ip
}

# Grafana Public IP
output "grafana_public_ip" {
  description = "Public IP address of the Grafana instance."
  value       = aws_instance.grafana.public_ip
}

# SSH Key Pair
output "key_pair_name" {
  description = "The name of the key pair used for SSH access."
  value       = var.key_pair_name
}
