terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "nexagrid-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "nexagrid-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
}

# ---------------------------------------------------------
# VPC & Networking (High Availability across 3 AZs)
# ---------------------------------------------------------
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "nexagrid-vpc-${var.environment}"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = false
  enable_vpn_gateway = false

  tags = var.common_tags
}

# ---------------------------------------------------------
# EKS Cluster (Elastic Kubernetes Service)
# For running FastAPI horizontally scaled pods
# ---------------------------------------------------------
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "nexagrid-cluster-${var.environment}"
  cluster_version = "1.28"

  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.private_subnets
  cluster_endpoint_public_access = true

  eks_managed_node_groups = {
    compute_nodes = {
      min_size     = 2
      max_size     = 10
      desired_size = 3
      instance_types = ["t3.xlarge"]
    }
    sandbox_nodes = {
      # Dedicated isolated nodes for code execution
      min_size     = 2
      max_size     = 20
      desired_size = 4
      instance_types = ["t3.large"]
      taints = {
        dedicated = {
          key    = "workload"
          value  = "sandbox"
          effect = "NO_SCHEDULE"
        }
      }
    }
  }

  tags = var.common_tags
}

# ---------------------------------------------------------
# PostgreSQL Database (Amazon RDS)
# ---------------------------------------------------------
module "db" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "nexagrid-pg-${var.environment}"

  engine               = "postgres"
  engine_version       = "15.4"
  family               = "postgres15" # DB parameter group
  major_engine_version = "15"         # DB option group
  instance_class       = "db.t4g.xlarge"

  allocated_storage     = 100
  max_allocated_storage = 500

  db_name  = "nexagrid"
  username = "nexagrid_admin"
  port     = 5432

  multi_az               = true
  db_subnet_group_name   = module.vpc.database_subnet_group
  vpc_security_group_ids = [aws_security_group.db_sg.id]

  maintenance_window      = "Mon:00:00-Mon:03:00"
  backup_window           = "03:00-06:00"
  backup_retention_period = 14

  tags = var.common_tags
}

# ---------------------------------------------------------
# Redis (Amazon ElastiCache for Pub/Sub & CRDT state)
# ---------------------------------------------------------
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id          = "nexagrid-redis-${var.environment}"
  description                   = "Redis cluster for NexaGrid WebSockets and Pub/Sub"
  node_type                     = "cache.t4g.medium"
  port                          = 6379
  parameter_group_name          = "default.redis7.cluster.on"
  automatic_failover_enabled    = true
  multi_az_enabled              = true
  num_node_groups               = 2
  replicas_per_node_group       = 2

  subnet_group_name          = aws_elasticache_subnet_group.redis_subnet.name
  security_group_ids         = [aws_security_group.redis_sg.id]

  tags = var.common_tags
}

resource "aws_elasticache_subnet_group" "redis_subnet" {
  name       = "nexagrid-redis-subnet-${var.environment}"
  subnet_ids = module.vpc.private_subnets
}

# Security Groups (Simplified for illustration)
resource "aws_security_group" "db_sg" {
  name        = "nexagrid-db-sg"
  description = "Allow EKS nodes to connect to RDS"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }
}

resource "aws_security_group" "redis_sg" {
  name        = "nexagrid-redis-sg"
  description = "Allow EKS nodes to connect to Redis"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }
}
