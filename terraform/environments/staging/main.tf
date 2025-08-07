terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }

  # Configure your backend here (e.g., S3 backend)
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "werewolf/staging/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = "staging"
      Project     = "werewolf-game"
      ManagedBy   = "terraform"
    }
  }
}

# Local values
locals {
  project_name = "werewolf"
  environment  = "staging"
  aws_region   = var.aws_region

  # Availability zones
  availability_zones = ["${var.aws_region}a", "${var.aws_region}b"]

  # Network CIDR blocks
  vpc_cidr             = "10.1.0.0/16"
  public_subnet_cidrs  = ["10.1.1.0/24", "10.1.2.0/24"]
  private_subnet_cidrs = ["10.1.10.0/24", "10.1.20.0/24"]
}

# Networking Module
module "networking" {
  source = "../../modules/networking"

  project_name           = local.project_name
  environment           = local.environment
  vpc_cidr              = local.vpc_cidr
  availability_zones    = local.availability_zones
  public_subnet_cidrs   = local.public_subnet_cidrs
  private_subnet_cidrs  = local.private_subnet_cidrs
}

# Secrets Module
module "secrets" {
  source = "../../modules/secrets"

  project_name         = local.project_name
  environment         = local.environment
  database_url        = "postgresql://${var.db_username}:${var.db_password}@${module.rds.db_instance_endpoint}/${var.db_name}"
  openai_api_key      = var.openai_api_key
  jwt_secret_key      = var.jwt_secret_key
  google_client_id    = var.google_client_id
  google_client_secret = var.google_client_secret
}

# RDS Module
module "rds" {
  source = "../../modules/rds"

  project_name           = local.project_name
  environment           = local.environment
  vpc_id                = module.networking.vpc_id
  vpc_cidr_block        = module.networking.vpc_cidr_block
  private_subnet_ids    = module.networking.private_subnet_ids
  db_instance_class     = "db.t3.small"
  db_name               = var.db_name
  db_username           = var.db_username
  db_password           = var.db_password
  allocated_storage     = 50
  max_allocated_storage = 200
  backup_retention_period = 7
  deletion_protection   = true
  skip_final_snapshot   = false
}

# ECS Module
module "ecs" {
  source = "../../modules/ecs"

  project_name              = local.project_name
  environment              = local.environment
  vpc_id                   = module.networking.vpc_id
  public_subnet_ids        = module.networking.public_subnet_ids
  private_subnet_ids       = module.networking.private_subnet_ids
  backend_image            = var.backend_image
  container_port           = 8000
  task_cpu                = "512"
  task_memory             = "1024"
  desired_count           = 2
  aws_region              = local.aws_region
  database_url_secret_arn = module.secrets.database_url_secret_arn
  secrets_manager_arns    = module.secrets.all_secret_arns

  depends_on = [module.rds, module.secrets]
}

# S3 Frontend Module
module "s3_frontend" {
  source = "../../modules/s3-frontend"

  project_name           = local.project_name
  environment           = local.environment
  domain_names           = var.domain_names
  acm_certificate_arn    = var.acm_certificate_arn
  cloudfront_price_class = "PriceClass_100"
}
