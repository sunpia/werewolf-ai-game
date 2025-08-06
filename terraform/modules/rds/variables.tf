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

variable "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "IDs of private subnets for RDS subnet group"
  type        = list(string)
}

variable "db_name" {
  description = "Name of the database"
  type        = string
  default     = "werewolf_game"
}

variable "engine_version" {
  description = "Aurora PostgreSQL engine version"
  type        = string
  default     = "15.8"
}

variable "db_username" {
  description = "Username for the database"
  type        = string
  default     = "werewolf_user"
}

variable "db_password" {
  description = "Password for the database (auto-generated from secrets module)"
  type        = string
  sensitive   = true
}

variable "min_aurora_capacity" {
  description = "Minimum Aurora capacity units (0.5 to 128)"
  type        = number
  default     = 0.5
}

variable "max_aurora_capacity" {
  description = "Maximum Aurora capacity units (0.5 to 128)"
  type        = number
  default     = 4
}

variable "backup_retention_period" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot when deleting"
  type        = bool
  default     = false
}
