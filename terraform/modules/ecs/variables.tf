variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (test, staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "public_subnet_ids" {
  description = "IDs of public subnets for ALB"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "IDs of private subnets for ECS tasks"
  type        = list(string)
}

variable "backend_image" {
  description = "Docker image for the backend service"
  type        = string
}

variable "container_port" {
  description = "Port that the container listens on"
  type        = number
  default     = 8000
}

variable "task_cpu" {
  description = "CPU units for the ECS task"
  type        = string
  default     = "256"
}

variable "task_memory" {
  description = "Memory for the ECS task"
  type        = string
  default     = "512"
}

variable "desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 1
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "database_url_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the database URL"
  type        = string
}

variable "api_keys_secret_arn" {
  description = "ARN of the Secrets Manager secret containing API keys"
  type        = string
}

variable "jwt_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the JWT secret"
  type        = string
}

variable "google_oauth_secret_arn" {
  description = "ARN of the Secrets Manager secret containing Google OAuth credentials"
  type        = string
}

variable "secrets_manager_arns" {
  description = "List of Secrets Manager ARNs that ECS tasks need access to"
  type        = list(string)
}
