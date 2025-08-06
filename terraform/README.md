# Werewolf Game - AWS Infrastructure

This repository contains Terraform configurations for deploying the Werewolf AI Game to AWS across multiple environments (test, staging, production).

## Architecture Overview

The infrastructure includes:

- **Backend**: FastAPI application deployed on AWS ECS Fargate
- **Frontend**: React application hosted on S3 with CloudFront CDN
- **Database**: PostgreSQL on AWS RDS
- **Secrets**: API keys and sensitive data stored in AWS Secrets Manager
- **Networking**: VPC with public/private subnets across multiple AZs
- **Load Balancing**: Application Load Balancer for backend services

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.0 installed
3. **Docker** for building and pushing container images
4. **AWS ECR repository** for storing Docker images (optional, can use Docker Hub)

## Project Structure

```
terraform/
├── environments/           # Environment-specific configurations
│   ├── test/              # Test environment
│   ├── staging/           # Staging environment
│   └── prod/              # Production environment
└── modules/               # Reusable Terraform modules
    ├── networking/        # VPC, subnets, routing
    ├── rds/              # PostgreSQL database
    ├── ecs/              # ECS cluster and services
    ├── s3-frontend/      # S3 bucket and CloudFront
    └── secrets/          # AWS Secrets Manager
```

## Environment Differences

| Component       | Test           | Staging        | Production     |
|----------------|----------------|----------------|----------------|
| RDS Instance   | db.t3.micro    | db.t3.small    | db.t3.medium   |
| ECS Task CPU   | 256            | 512            | 1024           |
| ECS Task Memory| 512 MB         | 1024 MB        | 2048 MB        |
| ECS Tasks      | 1              | 2              | 3              |
| Backup Retention| 3 days        | 7 days         | 30 days        |
| Deletion Protection| Disabled   | Enabled        | Enabled        |
| Availability Zones| 2           | 2              | 3              |

## Setup Instructions

### 1. Build and Push Docker Image

First, build and push your backend Docker image:

```bash
# Build the Docker image
docker build -t werewolf-backend .

# Tag for ECR (replace with your account ID and region)
docker tag werewolf-backend:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/werewolf-backend:latest

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/werewolf-backend:latest
```

### 2. Configure Terraform Backend (Recommended)

Create an S3 bucket for Terraform state storage:

```bash
aws s3 mb s3://your-terraform-state-bucket
aws s3api put-bucket-versioning --bucket your-terraform-state-bucket --versioning-configuration Status=Enabled
```

Update the backend configuration in each environment's `main.tf`:

```hcl
backend "s3" {
  bucket = "your-terraform-state-bucket"
  key    = "werewolf/test/terraform.tfstate"  # Change per environment
  region = "us-east-1"
}
```

### 3. Deploy Test Environment

```bash
cd terraform/environments/test

# Copy and configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your actual values

# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Apply the configuration
terraform apply
```

### 4. Deploy Staging Environment

```bash
cd terraform/environments/staging

# Copy and configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your actual values

# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Apply the configuration
terraform apply
```

### 5. Deploy Production Environment

```bash
cd terraform/environments/prod

# Copy and configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your actual values

# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Apply the configuration
terraform apply
```

## Configuration Variables

### Required Variables

- `backend_image`: Docker image URL for the backend service
- `db_password`: Database password (use strong passwords for staging/prod)
- `openai_api_key`: OpenAI API key for AI functionality
- `jwt_secret_key`: Secret key for JWT token signing
- `google_client_id`: Google OAuth client ID
- `google_client_secret`: Google OAuth client secret

### Optional Variables

- `aws_region`: AWS region (default: us-east-1)
- `domain_names`: Custom domain names for CloudFront
- `acm_certificate_arn`: SSL certificate ARN for custom domains

## Post-Deployment Steps

### 1. Upload Frontend to S3

After deployment, build and upload your React frontend:

```bash
cd frontend

# Install dependencies
npm install

# Build for production
REACT_APP_API_URL=https://your-backend-alb-url npm run build

# Upload to S3 (replace with your bucket name from terraform output)
aws s3 sync build/ s3://your-frontend-bucket-name --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
```

### 2. Initialize Database

Connect to your RDS instance and run any necessary database migrations or initialization scripts.

### 3. Update DNS (For Custom Domains)

If using custom domains, create CNAME records pointing to your CloudFront distribution.

## Monitoring and Logging

- **ECS Logs**: Available in CloudWatch under `/ecs/werewolf-{environment}/backend`
- **RDS Monitoring**: Performance Insights enabled for database monitoring
- **ALB Logs**: Can be enabled by modifying the ALB configuration

## Security Considerations

1. **Secrets**: All sensitive data is stored in AWS Secrets Manager
2. **Network**: Backend runs in private subnets with no direct internet access
3. **Database**: RDS instance is in private subnets and only accessible from VPC
4. **SSL/TLS**: HTTPS enforced on all public endpoints

## Troubleshooting

### Common Issues

1. **ECS Service fails to start**:
   - Check CloudWatch logs for error messages
   - Verify secrets are properly configured
   - Ensure database is accessible

2. **Frontend not loading**:
   - Check S3 bucket policy and CloudFront configuration
   - Verify build artifacts were uploaded correctly

3. **Database connection issues**:
   - Check security group rules
   - Verify database credentials in Secrets Manager

### Useful Commands

```bash
# Check ECS service status
aws ecs describe-services --cluster werewolf-{env}-cluster --services werewolf-{env}-backend-service

# View ECS logs
aws logs tail /ecs/werewolf-{env}/backend --follow

# Check RDS status
aws rds describe-db-instances --db-instance-identifier werewolf-{env}-postgres

# Sync frontend to S3
aws s3 sync frontend/build/ s3://bucket-name --delete
```

## Cleanup

To destroy the infrastructure:

```bash
cd terraform/environments/{environment}
terraform destroy
```

**Warning**: This will permanently delete all resources including databases. Make sure you have backups if needed.

## Cost Optimization

- **Test Environment**: Designed for minimal cost with small instance sizes
- **Auto Scaling**: ECS services can be configured with auto-scaling policies
- **Spot Instances**: Consider using Spot instances for non-production workloads
- **Storage Optimization**: Use appropriate storage classes for S3 and RDS

## Contributing

1. Create feature branches for infrastructure changes
2. Test changes in the test environment first
3. Use `terraform plan` to review changes before applying
4. Document any new variables or modules

## Support

For issues with the infrastructure setup, please check:

1. AWS documentation for service-specific issues
2. Terraform documentation for configuration problems
3. CloudWatch logs for runtime issues
