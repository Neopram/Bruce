resource "aws_instance" "prometheus" {
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = aws_subnet.public.id
  tags = {
    Name = "PrometheusInstance"
  }
  user_data = <<-EOT
              #!/bin/bash
              apt-get update -y
              apt-get install -y prometheus
              systemctl start prometheus
              EOT
}

resource "aws_instance" "grafana" {
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = aws_subnet.public.id
  tags = {
    Name = "GrafanaInstance"
  }
  user_data = <<-EOT
              #!/bin/bash
              apt-get update -y
              apt-get install -y grafana
              systemctl start grafana-server
              EOT
}
