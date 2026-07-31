# NexaGrid Terraform Infrastructure-as-Code Spec (AWS Deployment)
# Enterprise Cloud Architecture for Real-Time WebSocket & CRDT Platform

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

# 1. Virtual Private Cloud (VPC) & Subnets
resource "aws_vpc" "nexagrid_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name = "nexagrid-vpc"
  }
}

# 2. Application Load Balancer (ALB) with WSS Sticky Sessions
resource "aws_lb" "nexagrid_alb" {
  name               = "nexagrid-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = [aws_subnet.public_1.id, aws_subnet.public_2.id]
}

resource "aws_lb_target_group" "nexagrid_tg" {
  name        = "nexagrid-backend-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.nexagrid_vpc.id
  target_type = "ip"

  health_check {
    path                = "/health"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = true
  }
}

# 3. Amazon ElastiCache Redis Cluster (Pub/Sub & Presence Cache)
resource "aws_elasticache_cluster" "nexagrid_redis" {
  cluster_id           = "nexagrid-redis"
  engine               = "redis"
  node_type            = "cache.t4g.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
}

# 4. Amazon RDS Aurora PostgreSQL Multi-AZ Database Cluster
resource "aws_rds_cluster" "nexagrid_postgres" {
  cluster_identifier      = "nexagrid-db-cluster"
  engine                  = "aurora-postgresql"
  engine_version          = "15.4"
  database_name           = "nexagrid"
  master_username         = "nexagrid_admin"
  master_password         = "SuperSecurePassword2026!"
  backup_retention_period = 7
  preferred_backup_window = "07:00-09:00"
}

# 5. AWS ECS Fargate Task Definition & Service
resource "aws_ecs_cluster" "nexagrid_cluster" {
  name = "nexagrid-ecs-cluster"
}

resource "aws_ecs_task_definition" "nexagrid_task" {
  family                   = "nexagrid-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"

  container_definitions = jsonencode([
    {
      name      = "nexagrid-api"
      image     = "nexagrid-backend:latest"
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
        }
      ]
      environment = [
        { name = "DATABASE_URL", value = "postgresql://nexagrid_admin:SuperSecurePassword2026!@${aws_rds_cluster.nexagrid_postgres.endpoint}:5432/nexagrid" },
        { name = "REDIS_URL", value = "redis://${aws_elasticache_cluster.nexagrid_redis.cache_nodes[0].address}:6379/0" }
      ]
    }
  ])
}

resource "aws_security_group" "alb_sg" {
  name   = "nexagrid-alb-sg"
  vpc_id = aws_vpc.nexagrid_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.nexagrid_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true
}

resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.nexagrid_vpc.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = true
}
