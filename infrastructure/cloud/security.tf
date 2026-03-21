# Security Configuration for Trading Bot Infrastructure

# Security Group for Trading Bot Instances
resource "aws_security_group" "trading_bot_sg" {
  name        = "trading-bot-sg"
  description = "Allow inbound traffic to the trading bot"
  vpc_id      = aws_vpc.trading_bot_vpc.id

  # Ingress rules for trading bot
  ingress {
    description      = "HTTP access for trading bot"
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = [var.allowed_ip]
  }

  ingress {
    description      = "SSH access for management"
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = [var.allowed_ip]
  }

  # Egress rules (allow all outbound traffic)
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name = "TradingBotSecurityGroup"
  }
}

# Security Group for Monitoring Instances (Prometheus & Grafana)
resource "aws_security_group" "monitoring_sg" {
  name        = "monitoring-sg"
  description = "Allow inbound traffic for monitoring tools"
  vpc_id      = aws_vpc.trading_bot_vpc.id

  ingress {
    description      = "Prometheus HTTP"
    from_port        = 9090
    to_port          = 9090
    protocol         = "tcp"
    cidr_blocks      = [var.allowed_ip]
  }

  ingress {
    description      = "Grafana HTTP"
    from_port        = 3000
    to_port          = 3000
    protocol         = "tcp"
    cidr_blocks      = [var.allowed_ip]
  }

  # Egress rules (allow all outbound traffic)
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name = "MonitoringSecurityGroup"
  }
}

# Outputs for Security Groups
output "trading_bot_security_group_id" {
  description = "ID of the Trading Bot Security Group"
  value       = aws_security_group.trading_bot_sg.id
}

output "monitoring_security_group_id" {
  description = "ID of the Monitoring Security Group"
  value       = aws_security_group.monitoring_sg.id
}
