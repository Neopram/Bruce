resource "aws_autoscaling_group" "asg" {
  launch_configuration = aws_launch_configuration.aslc.id
  min_size             = var.min_capacity
  max_size             = var.max_capacity
  desired_capacity     = var.desired_capacity
  vpc_zone_identifier  = [aws_subnet.public.id]
  tags = [{
    key                 = "Name"
    value               = "AutoScalingGroup"
    propagate_at_launch = true
  }]
}

resource "aws_launch_configuration" "aslc" {
  image_id      = var.ami_id
  instance_type = var.instance_type
  security_groups = [aws_security_group.trading_bot_sg.id]

  user_data = <<-EOT
              #!/bin/bash
              apt-get update -y
              docker run -d -p 80:80 trading-bot:latest
              EOT
}
