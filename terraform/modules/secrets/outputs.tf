output "database_password" {
  description = "Generated database password"
  value       = var.db_password
  sensitive   = true
}

output "database_password_secret_arn" {
  description = "ARN of the database password secret"
  value       = aws_secretsmanager_secret.database_password.arn
}

output "database_url_secret_arn" {
  description = "ARN of the database URL secret"
  value       = aws_secretsmanager_secret.database_url.arn
}

output "api_keys_secret_arn" {
  description = "ARN of the API keys secret"
  value       = aws_secretsmanager_secret.api_keys.arn
}

output "jwt_secret_arn" {
  description = "ARN of the JWT secret"
  value       = aws_secretsmanager_secret.jwt_secret.arn
}

output "google_oauth_secret_arn" {
  description = "ARN of the Google OAuth secret"
  value       = aws_secretsmanager_secret.google_oauth.arn
}

output "all_secret_arns" {
  description = "List of all secret ARNs"
  value = [
    aws_secretsmanager_secret.database_password.arn,
    aws_secretsmanager_secret.database_url.arn,
    aws_secretsmanager_secret.api_keys.arn,
    aws_secretsmanager_secret.jwt_secret.arn,
    aws_secretsmanager_secret.google_oauth.arn
  ]
}
