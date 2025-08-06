variable "environment" {
  description = "Environment name (test, staging, prod)"
  type        = string
  default     = "test"
}

variable "config_file" {
  description = "Path to the JSON configuration file"
  type        = string
  default     = ""
}

# Database credentials (should be passed via environment variables or tfvars)
variable "db_username" {
  description = "Database username"
  type        = string
  default     = "werewolf_user"
}

# Note: db_password is now auto-generated and stored in AWS Secrets Manager

# API Keys and Secrets (should be passed via environment variables or tfvars)
variable "openai_api_key" {
  description = "OpenAI API key (will be empty initially, update in AWS Secrets Manager)"
  type        = string
  default     = ""
  sensitive   = true
}

# Note: jwt_secret_key is now auto-generated and stored in AWS Secrets Manager

variable "google_client_id" {
  description = "Google OAuth Client ID"
  type        = string
  default     = "650648943441-jtl94n3c42n9ad6da88j9800hhlunfnj.apps.googleusercontent.com"
  sensitive   = true
}

variable "google_client_secret" {
  description = "Google OAuth Client Secret (will be empty initially, update in AWS Secrets Manager)"
  type        = string
  default     = ""
  sensitive   = true
}

# Backend Docker image
variable "backend_image" {
  description = "Docker image for the backend service"
  type        = string
  default     = "dockerofshy/ai-werewolf-game:34a114"
}

# SSL Certificate ARN (optional)
variable "acm_certificate_arn" {
  description = "ARN of the ACM certificate for HTTPS"
  type        = string
  default     = ""
}
