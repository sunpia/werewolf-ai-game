# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-subnet-group"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Security Group for Aurora
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-${var.environment}-aurora-sg"
  description = "Security group for Aurora PostgreSQL Serverless"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-aurora-sg"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Aurora Cluster Parameter Group
resource "aws_rds_cluster_parameter_group" "main" {
  family      = "aurora-postgresql15"
  name        = "${var.project_name}-${var.environment}-aurora-cluster-params"
  description = "Aurora cluster parameter group for PostgreSQL 15"

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-aurora-cluster-params"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Aurora DB Parameter Group for instances
resource "aws_db_parameter_group" "main" {
  family = "aurora-postgresql15"
  name   = "${var.project_name}-${var.environment}-aurora-db-params"

  tags = {
    Name        = "${var.project_name}-${var.environment}-aurora-db-params"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Aurora Serverless v2 Cluster
resource "aws_rds_cluster" "main" {
  cluster_identifier = "${var.project_name}-${var.environment}-aurora-cluster"

  # Engine options
  engine         = "aurora-postgresql"
  engine_version = var.engine_version
  engine_mode    = "provisioned"

  # Database options
  database_name   = var.db_name
  master_username = var.db_username
  master_password = var.db_password
  port            = 5432

  # Network & Security
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  # Serverless v2 scaling configuration
  serverlessv2_scaling_configuration {
    max_capacity = var.max_aurora_capacity
    min_capacity = var.min_aurora_capacity
  }

  # Backup & Maintenance
  backup_retention_period = var.backup_retention_period
  preferred_backup_window = "03:00-04:00"
  preferred_maintenance_window = "Sun:04:00-Sun:05:00"
  copy_tags_to_snapshot = true

  # Storage
  storage_encrypted = true

  # Parameter groups
  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.main.name

  # Deletion protection
  deletion_protection = var.deletion_protection
  skip_final_snapshot = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.project_name}-${var.environment}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  tags = {
    Name        = "${var.project_name}-${var.environment}-aurora-cluster"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Aurora Serverless v2 Instance
resource "aws_rds_cluster_instance" "main" {
  identifier         = "${var.project_name}-${var.environment}-aurora-instance"
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version

  # Parameter group
  db_parameter_group_name = aws_db_parameter_group.main.name

  # Performance Insights
  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn        = aws_iam_role.rds_monitoring.arn

  tags = {
    Name        = "${var.project_name}-${var.environment}-aurora-instance"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Role for RDS Enhanced Monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "${var.project_name}-${var.environment}-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-rds-monitoring-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Attach policy to the monitoring role
resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}
