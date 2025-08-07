output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.db_instance_endpoint
}

output "backend_alb_dns_name" {
  description = "DNS name of the backend Application Load Balancer"
  value       = module.ecs.alb_dns_name
}

output "backend_url" {
  description = "URL of the backend API"
  value       = "http://${module.ecs.alb_dns_name}"
}

output "frontend_s3_bucket" {
  description = "S3 bucket name for frontend"
  value       = module.s3_frontend.s3_bucket_name
}

output "frontend_cloudfront_domain" {
  description = "CloudFront distribution domain name"
  value       = module.s3_frontend.cloudfront_domain_name
}

output "frontend_url" {
  description = "URL of the frontend website"
  value       = module.s3_frontend.website_url
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "secrets_arns" {
  description = "ARNs of all secrets"
  value = {
    database_url = module.secrets.database_url_secret_arn
    api_keys     = module.secrets.api_keys_secret_arn
    jwt_secret   = module.secrets.jwt_secret_arn
    google_oauth = module.secrets.google_oauth_secret_arn
  }
}
