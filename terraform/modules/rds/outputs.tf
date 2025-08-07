output "db_cluster_id" {
  description = "Aurora cluster ID"
  value       = aws_rds_cluster.main.id
}

output "db_instance_endpoint" {
  description = "Aurora cluster writer endpoint"
  value       = aws_rds_cluster.main.endpoint
}

output "db_reader_endpoint" {
  description = "Aurora cluster reader endpoint"
  value       = aws_rds_cluster.main.reader_endpoint
}

output "db_instance_port" {
  description = "Aurora cluster port"
  value       = aws_rds_cluster.main.port
}

output "db_instance_arn" {
  description = "Aurora cluster ARN"
  value       = aws_rds_cluster.main.arn
}

output "db_security_group_id" {
  description = "Security group ID for Aurora"
  value       = aws_security_group.rds.id
}

output "database_url" {
  description = "Database connection URL"
  value       = "postgresql://${var.db_username}:${var.db_password}@${aws_rds_cluster.main.endpoint}/${var.db_name}"
  sensitive   = true
}
