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

  backend "s3" {
    bucket = "werewolf-game-tf-state"
    region = "eu-central-1"
    encrypt = true
  }
}

# Load configuration from JSON file
locals {
  config_file = var.config_file != "" ? var.config_file : "config/${var.environment}.json"
  config      = jsondecode(file(local.config_file))
  
  # Extract configuration values
  project_name = local.config.project_name
  environment  = local.config.environment
  aws_region   = local.config.aws_region
  
  # Network configuration
  vpc_cidr             = local.config.networking.vpc_cidr
  availability_zones   = local.config.networking.availability_zones
  public_subnet_cidrs  = local.config.networking.public_subnet_cidrs
  private_subnet_cidrs = local.config.networking.private_subnet_cidrs
  
  # Database configuration
  db_config = local.config.database
  
  # ECS configuration
  ecs_config = local.config.ecs
  
  # Frontend configuration
  frontend_config = local.config.frontend
}

provider "aws" {
  region = local.aws_region

  default_tags {
    tags = {
      Environment = local.environment
      Project     = local.project_name
      ManagedBy   = "terraform"
    }
  }
}

# Networking Module
module "networking" {
  source = "./modules/networking"

  project_name           = local.project_name
  environment           = local.environment
  vpc_cidr              = local.vpc_cidr
  availability_zones    = local.availability_zones
  public_subnet_cidrs   = local.public_subnet_cidrs
  private_subnet_cidrs  = local.private_subnet_cidrs
}

# Generate database password first
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Generate JWT secret key
resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

# Aurora Module (formerly RDS)
module "rds" {
  source = "./modules/rds"

  project_name            = local.project_name
  environment            = local.environment
  vpc_id                 = module.networking.vpc_id
  vpc_cidr_block         = module.networking.vpc_cidr_block
  private_subnet_ids     = module.networking.private_subnet_ids
  db_name                = local.db_config.db_name
  engine_version         = try(local.db_config.engine_version, "15.8")
  db_username            = var.db_username
  db_password            = random_password.db_password.result
  min_aurora_capacity    = try(local.db_config.min_aurora_capacity, 0.5)
  max_aurora_capacity    = try(local.db_config.max_aurora_capacity, 4)
  backup_retention_period = local.db_config.backup_retention_period
  deletion_protection    = local.db_config.deletion_protection
  skip_final_snapshot    = local.db_config.skip_final_snapshot
}

# Secrets Module (created after RDS to get endpoint)
module "secrets" {
  source = "./modules/secrets"

  project_name     = local.project_name
  environment     = local.environment
  db_name         = local.db_config.db_name
  db_username     = var.db_username
  db_password     = random_password.db_password.result
  db_endpoint     = module.rds.db_instance_endpoint
  openai_api_key  = var.openai_api_key
  jwt_secret_key  = random_password.jwt_secret.result
  google_client_id    = var.google_client_id
  google_client_secret = var.google_client_secret

  depends_on = [module.rds]
}

# ECS Module
module "ecs" {
  source = "./modules/ecs"

  project_name              = local.project_name
  environment              = local.environment
  vpc_id                   = module.networking.vpc_id
  public_subnet_ids        = module.networking.public_subnet_ids
  private_subnet_ids       = module.networking.private_subnet_ids
  backend_image            = var.backend_image
  container_port           = local.ecs_config.container_port
  task_cpu                = local.ecs_config.task_cpu
  task_memory             = local.ecs_config.task_memory
  desired_count           = local.ecs_config.desired_count
  aws_region              = local.aws_region
  database_url_secret_arn = module.secrets.database_url_secret_arn
  api_keys_secret_arn     = module.secrets.api_keys_secret_arn
  jwt_secret_arn          = module.secrets.jwt_secret_arn
  google_oauth_secret_arn = module.secrets.google_oauth_secret_arn
  secrets_manager_arns    = module.secrets.all_secret_arns

  depends_on = [module.rds, module.secrets]
}

# S3 Frontend Module
module "s3_frontend" {
  source = "./modules/s3-frontend"

  project_name           = local.project_name
  environment           = local.environment
  domain_names           = local.frontend_config.domain_names
  acm_certificate_arn    = var.acm_certificate_arn
  cloudfront_price_class = local.frontend_config.cloudfront_price_class
  
  # ALB configuration for API routing
  alb_dns_name      = module.ecs.alb_dns_name
  alb_https_enabled = false  # Set to true when HTTPS is enabled on ALB

  depends_on = [module.ecs]
}
