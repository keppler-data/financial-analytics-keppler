# Terraform main configuration for AWS infrastructure

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Backend configuration for state management
  backend "s3" {
    bucket         = "financial-risk-lakehouse-terraform-state"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "financial-risk-lakehouse"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# S3 bucket for data lake
resource "aws_s3_bucket" "data_lake" {
  bucket = "financial-risk-lakehouse-${var.environment}"
  
  tags = {
    Name = "Financial Risk Lakehouse Data Lake"
  }
}

# EMR Cluster for Spark jobs
resource "aws_emr_cluster" "spark_cluster" {
  name            = "financial-risk-spark-${var.environment}"
  release_label  = "emr-7.0.0"
  service_role   = aws_iam_role.emr_service_role.arn
  
  ec2_attributes {
    instance_profile = aws_iam_instance_profile.emr_instance_profile.arn
    key_name         = var.emr_key_pair
  }
  
  master_node_type_count = 1
  core_node_type_count   = var.emr_core_node_count
  
  master_instance_group {
    instance_type = var.master_instance_type
  }
  
  core_instance_group {
    instance_type = var.core_instance_type
  }
  
  tags = {
    Name = "Spark Cluster"
  }
}

# RDS PostgreSQL instance
resource "aws_db_instance" "airflow_db" {
  identifier     = "financial-risk-airflow-${var.environment}"
  engine         = "postgres"
  engine_version = "15.3"
  instance_class = var.db_instance_class
  
  allocated_storage = var.db_allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true
  
  db_name  = var.db_name
  username = var.db_username
  password = random_password.db_password.result
  
  skip_final_snapshot = var.environment != "prod"
  
  tags = {
    Name = "Airflow Database"
  }
}

# Random password for database
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "emr_core_node_count" {
  description = "Number of core nodes in EMR cluster"
  type        = number
  default     = 3
}

variable "master_instance_type" {
  description = "EMR master node instance type"
  type        = string
  default     = "m6i.xlarge"
}

variable "core_instance_type" {
  description = "EMR core node instance type"
  type        = string
  default     = "m6i.xlarge"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.medium"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "RDS database name"
  type        = string
  default     = "airflow"
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "airflow"
  sensitive   = true
}

variable "emr_key_pair" {
  description = "EC2 key pair for EMR cluster"
  type        = string
}

# IAM role for EMR
resource "aws_iam_role" "emr_service_role" {
  name = "financial-risk-emr-service-role-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "elasticmapreduce.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "emr_service_policy" {
  role       = aws_iam_role.emr_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceRole"
}

# IAM instance profile for EMR
resource "aws_iam_instance_profile" "emr_instance_profile" {
  name = "financial-risk-emr-instance-profile-${var.environment}"
  role = aws_iam_role.emr_instance_role.name
}

resource "aws_iam_role" "emr_instance_role" {
  name = "financial-risk-emr-instance-role-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "emr_instance_policy" {
  role       = aws_iam_role.emr_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceforEC2Role"
}

# Outputs
output "data_lake_bucket" {
  value = aws_s3_bucket.data_lake.id
}

output "emr_cluster_id" {
  value = aws_emr_cluster.spark_cluster.id
}

output "db_endpoint" {
  value = aws_db_instance.airflow_db.endpoint
}
