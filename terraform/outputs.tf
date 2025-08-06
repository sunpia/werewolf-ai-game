# Networking outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.networking.private_subnet_ids
}

# Database outputs
output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.db_instance_endpoint
}

output "database_password" {
  description = "Auto-generated database password (for initial setup only)"
  value       = random_password.db_password.result
  sensitive   = true
}

output "jwt_secret_key" {
  description = "Auto-generated JWT secret key (for initial setup only)"
  value       = random_password.jwt_secret.result
  sensitive   = true
}

# ECS outputs
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.ecs.alb_dns_name
}

output "backend_url" {
  description = "Backend API URL"
  value       = "http://${module.ecs.alb_dns_name}"
}

# Frontend outputs
output "s3_bucket_name" {
  description = "Name of the S3 bucket for frontend"
  value       = module.s3_frontend.s3_bucket_name
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.s3_frontend.cloudfront_domain_name
}

output "frontend_url" {
  description = "Frontend URL"
  value       = "https://${module.s3_frontend.cloudfront_domain_name}"
}

# Secrets outputs
output "secrets_arns" {
  description = "ARNs of all secrets"
  value       = module.secrets.all_secret_arns
  sensitive   = true
}

output "google_client_secret_update_command" {
  description = "Command to update Google client secret in AWS Secrets Manager"
  value = "aws secretsmanager update-secret --secret-id ${module.secrets.google_oauth_secret_arn} --secret-string '{\"GOOGLE_CLIENT_ID\":\"${var.google_client_id}\",\"GOOGLE_CLIENT_SECRET\":\"YOUR_ACTUAL_SECRET_HERE\"}'"
  sensitive = true
}

output "openai_api_key_update_command" {
  description = "Command to update OpenAI API key in AWS Secrets Manager"
  value = "aws secretsmanager update-secret --secret-id ${module.secrets.api_keys_secret_arn} --secret-string '{\"OPENAI_API_KEY\":\"sk-your-actual-openai-key-here\"}'"
  sensitive = true
}
