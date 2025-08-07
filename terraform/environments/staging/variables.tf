variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "backend_image" {
  description = "Docker image for the backend service"
  type        = string
}

# Database variables
variable "db_name" {
  description = "Name of the database"
  type        = string
  default     = "werewolf_game"
}

variable "db_username" {
  description = "Username for the database"
  type        = string
  default     = "werewolf_user"
}

variable "db_password" {
  description = "Password for the database"
  type        = string
  sensitive   = true
}

# Secret variables
variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "JWT secret key"
  type        = string
  sensitive   = true
}

variable "google_client_id" {
  description = "Google OAuth client ID"
  type        = string
  sensitive   = true
}

variable "google_client_secret" {
  description = "Google OAuth client secret"
  type        = string
  sensitive   = true
}

# Domain and SSL variables
variable "domain_names" {
  description = "List of domain names for CloudFront distribution"
  type        = list(string)
  default     = []
}

variable "acm_certificate_arn" {
  description = "ARN of the ACM certificate for HTTPS"
  type        = string
  default     = ""
}
