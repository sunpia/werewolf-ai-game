#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    printf "${1}${2}${NC}\n"
}

# Function to show usage
usage() {
    echo "Usage: $0 <command> <environment> [options]"
    echo ""
    echo "Commands:"
    echo "  plan     - Create an execution plan"
    echo "  apply    - Apply the execution plan"
    echo "  destroy  - Destroy the infrastructure"
    echo "  init     - Initialize Terraform"
    echo "  validate - Validate Terraform configuration"
    echo "  output   - Show output values"
    echo ""
    echo "Environments:"
    echo "  test     - Test environment"
    echo "  staging  - Staging environment"
    echo "  prod     - Production environment"
    echo ""
    echo "Options:"
    echo "  --auto-approve  - Skip interactive approval (for apply/destroy)"
    echo "  --backend-config=<file> - Specify backend configuration file"
    echo ""
    echo "Examples:"
    echo "  $0 init staging"
    echo "  $0 plan test"
    echo "  $0 apply staging --auto-approve"
    echo "  $0 destroy test"
    echo ""
    echo "Environment Variables (required for sensitive values):"
    echo "  TF_VAR_db_password - Database password"
    echo "  TF_VAR_openai_api_key - OpenAI API key"
    echo "  TF_VAR_jwt_secret_key - JWT secret key"
    echo "  TF_VAR_google_client_id - Google OAuth Client ID"
    echo "  TF_VAR_google_client_secret - Google OAuth Client Secret"
    echo ""
    exit 1
}

# Check if correct number of arguments
if [ $# -lt 2 ]; then
    usage
fi

COMMAND=$1
ENVIRONMENT=$2
shift 2

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(test|staging|prod)$ ]]; then
    print_color $RED "Error: Invalid environment. Must be 'test', 'staging', or 'prod'"
    exit 1
fi

# Check if config files exist
CONFIG_FILE="config/${ENVIRONMENT}.json"
TFVARS_FILE="config/${ENVIRONMENT}.tfvars"

if [ ! -f "$CONFIG_FILE" ]; then
    print_color $RED "Error: Configuration file $CONFIG_FILE not found"
    exit 1
fi

if [ ! -f "$TFVARS_FILE" ]; then
    print_color $RED "Error: Variables file $TFVARS_FILE not found"
    exit 1
fi

# Parse additional options
AUTO_APPROVE=""
BACKEND_CONFIG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --auto-approve)
            AUTO_APPROVE="-auto-approve"
            shift
            ;;
        --backend-config=*)
            BACKEND_CONFIG="-backend-config=${1#*=}"
            shift
            ;;
        *)
            print_color $RED "Unknown option: $1"
            usage
            ;;
    esac
done

# Set workspace based on environment
WORKSPACE="${ENVIRONMENT}"

print_color $BLUE "=== Terraform Deployment Script ==="
print_color $BLUE "Environment: $ENVIRONMENT"
print_color $BLUE "Command: $COMMAND"
print_color $BLUE "Config File: $CONFIG_FILE"
print_color $BLUE "Variables File: $TFVARS_FILE"
echo ""

# Check required environment variables for sensitive operations
if [[ "$COMMAND" == "apply" || "$COMMAND" == "plan" ]]; then
    MISSING_VARS=""
    
    if [ -z "$TF_VAR_db_password" ]; then
        MISSING_VARS="$MISSING_VARS TF_VAR_db_password"
    fi
    
    if [ -z "$TF_VAR_openai_api_key" ]; then
        MISSING_VARS="$MISSING_VARS TF_VAR_openai_api_key"
    fi
    
    if [ -z "$TF_VAR_jwt_secret_key" ]; then
        MISSING_VARS="$MISSING_VARS TF_VAR_jwt_secret_key"
    fi
    
    if [ -z "$TF_VAR_google_client_id" ]; then
        MISSING_VARS="$MISSING_VARS TF_VAR_google_client_id"
    fi
    
    if [ -z "$TF_VAR_google_client_secret" ]; then
        MISSING_VARS="$MISSING_VARS TF_VAR_google_client_secret"
    fi
    
    if [ -n "$MISSING_VARS" ]; then
        print_color $RED "Error: Missing required environment variables:"
        for var in $MISSING_VARS; do
            print_color $RED "  - $var"
        done
        echo ""
        print_color $YELLOW "Please set these environment variables before running $COMMAND"
        exit 1
    fi
fi

# Execute Terraform commands
case $COMMAND in
    init)
        print_color $GREEN "Initializing Terraform..."
        if [ -n "$BACKEND_CONFIG" ]; then
            terraform init $BACKEND_CONFIG
        else
            terraform init
        fi
        
        print_color $GREEN "Setting up workspace: $WORKSPACE"
        terraform workspace select $WORKSPACE 2>/dev/null || terraform workspace new $WORKSPACE
        ;;
        
    validate)
        print_color $GREEN "Validating Terraform configuration..."
        terraform validate
        ;;
        
    plan)
        print_color $GREEN "Creating execution plan for $ENVIRONMENT..."
        terraform workspace select $WORKSPACE
        terraform plan -var-file="$TFVARS_FILE" -out="${ENVIRONMENT}.tfplan"
        ;;
        
    apply)
        print_color $GREEN "Applying changes for $ENVIRONMENT..."
        terraform workspace select $WORKSPACE
        
        if [ -f "${ENVIRONMENT}.tfplan" ]; then
            terraform apply $AUTO_APPROVE "${ENVIRONMENT}.tfplan"
        else
            print_color $YELLOW "No plan file found. Creating plan and applying..."
            terraform apply $AUTO_APPROVE -var-file="$TFVARS_FILE"
        fi
        ;;
        
    destroy)
        print_color $YELLOW "WARNING: This will destroy all resources in $ENVIRONMENT environment!"
        if [ -z "$AUTO_APPROVE" ]; then
            read -p "Are you sure you want to continue? (yes/no): " confirm
            if [ "$confirm" != "yes" ]; then
                print_color $BLUE "Operation cancelled."
                exit 0
            fi
        fi
        
        print_color $RED "Destroying infrastructure for $ENVIRONMENT..."
        terraform workspace select $WORKSPACE
        terraform destroy $AUTO_APPROVE -var-file="$TFVARS_FILE"
        ;;
        
    output)
        print_color $GREEN "Showing outputs for $ENVIRONMENT..."
        terraform workspace select $WORKSPACE
        terraform output
        ;;
        
    *)
        print_color $RED "Error: Unknown command '$COMMAND'"
        usage
        ;;
esac

print_color $GREEN "✅ Command '$COMMAND' completed successfully for environment '$ENVIRONMENT'"

# Werewolf Game Deployment Script
# Usage: ./deploy.sh [environment] [action]
# Example: ./deploy.sh staging deploy

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
ENVIRONMENT="${1:-test}"
ACTION="${2:-deploy}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(test|staging|prod)$ ]]; then
    echo "Error: Invalid environment '$ENVIRONMENT'. Must be: test, staging, or prod"
    exit 1
fi

# Validate action
if [[ ! "$ACTION" =~ ^(plan|deploy|destroy|status)$ ]]; then
    echo "Error: Invalid action '$ACTION'. Must be: plan, deploy, destroy, or status"
    exit 1
fi

echo "=========================================="
echo "Werewolf Game Deployment"
echo "Environment: $ENVIRONMENT"
echo "Action: $ACTION"
echo "=========================================="

# Check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Check if AWS CLI is installed and configured
    if ! command -v aws &> /dev/null; then
        echo "Error: AWS CLI is not installed"
        exit 1
    fi
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        echo "Error: Terraform is not installed"
        exit 1
    fi
    
    # Check if Docker is installed (for deploy action)
    if [[ "$ACTION" == "deploy" ]] && ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        echo "Error: AWS credentials not configured or invalid"
        exit 1
    fi
    
    # Check if terraform.tfvars exists
    if [[ ! -f "$SCRIPT_DIR/environments/$ENVIRONMENT/terraform.tfvars" ]]; then
        echo "Error: terraform.tfvars not found for $ENVIRONMENT environment"
        echo "Please copy terraform.tfvars.example to terraform.tfvars and configure it"
        exit 1
    fi
    
    echo "Prerequisites check passed ✓"
}

# Initialize Terraform
init_terraform() {
    echo "Initializing Terraform..."
    cd "$SCRIPT_DIR/environments/$ENVIRONMENT"
    terraform init
    echo "Terraform initialized ✓"
}

# Build and push Docker image
build_and_push_image() {
    echo "Building and pushing Docker image..."
    
    # Get AWS account ID and region
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=$(aws configure get region || echo "us-east-1")
    ECR_REPOSITORY="werewolf-backend"
    IMAGE_TAG="latest"
    
    # Full image name
    DOCKER_IMAGE="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"
    
    # Create ECR repository if it doesn't exist
    aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION 2>/dev/null || echo "ECR repository already exists"
    
    # Build Docker image
    echo "Building Docker image..."
    cd "$PROJECT_ROOT"
    docker build -t $DOCKER_IMAGE .
    
    # Login to ECR
    echo "Logging in to ECR..."
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
    
    # Push image
    echo "Pushing Docker image..."
    docker push $DOCKER_IMAGE
    
    echo "Docker image built and pushed ✓"
}

# Deploy infrastructure
deploy_infrastructure() {
    echo "Deploying infrastructure..."
    cd "$SCRIPT_DIR/environments/$ENVIRONMENT"
    
    # Plan first
    echo "Running terraform plan..."
    terraform plan -out=tfplan
    
    # Apply
    echo "Applying Terraform configuration..."
    terraform apply tfplan
    rm -f tfplan
    
    echo "Infrastructure deployed ✓"
}

# Build and deploy frontend
deploy_frontend() {
    echo "Building and deploying frontend..."
    
    cd "$PROJECT_ROOT/frontend"
    
    # Install dependencies
    echo "Installing frontend dependencies..."
    npm install
    
    # Get backend URL from Terraform output
    cd "$SCRIPT_DIR/environments/$ENVIRONMENT"
    BACKEND_URL=$(terraform output -raw backend_url)
    
    # Build frontend with backend URL
    echo "Building frontend with backend URL: $BACKEND_URL"
    cd "$PROJECT_ROOT/frontend"
    REACT_APP_API_URL="$BACKEND_URL" npm run build
    
    # Get S3 bucket name and CloudFront distribution ID
    cd "$SCRIPT_DIR/environments/$ENVIRONMENT"
    S3_BUCKET=$(terraform output -raw frontend_s3_bucket)
    CLOUDFRONT_DOMAIN=$(terraform output -raw frontend_cloudfront_domain)
    
    # Upload to S3
    echo "Uploading frontend to S3 bucket: $S3_BUCKET"
    cd "$PROJECT_ROOT/frontend"
    aws s3 sync build/ s3://$S3_BUCKET --delete
    
    # Get CloudFront distribution ID (extract from domain)
    DISTRIBUTION_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?DomainName=='$CLOUDFRONT_DOMAIN'].Id" --output text)
    
    if [[ -n "$DISTRIBUTION_ID" ]]; then
        echo "Creating CloudFront invalidation for distribution: $DISTRIBUTION_ID"
        aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"
    fi
    
    echo "Frontend deployed ✓"
}

# Show infrastructure status
show_status() {
    echo "Infrastructure status for $ENVIRONMENT environment:"
    echo "=================================================="
    cd "$SCRIPT_DIR/environments/$ENVIRONMENT"
    
    if [[ -f "terraform.tfstate" ]]; then
        terraform output
    else
        echo "No infrastructure deployed yet"
    fi
}

# Main execution
main() {
    check_prerequisites
    
    case $ACTION in
        "plan")
            init_terraform
            cd "$SCRIPT_DIR/environments/$ENVIRONMENT"
            terraform plan
            ;;
        "deploy")
            init_terraform
            build_and_push_image
            deploy_infrastructure
            deploy_frontend
            echo ""
            echo "=========================================="
            echo "Deployment completed successfully! 🎉"
            echo "=========================================="
            show_status
            ;;
        "destroy")
            init_terraform
            cd "$SCRIPT_DIR/environments/$ENVIRONMENT"
            echo "⚠️  WARNING: This will destroy all infrastructure for $ENVIRONMENT environment!"
            read -p "Are you sure? (type 'yes' to continue): " -r
            if [[ $REPLY == "yes" ]]; then
                terraform destroy
                echo "Infrastructure destroyed"
            else
                echo "Destroy cancelled"
            fi
            ;;
        "status")
            show_status
            ;;
    esac
}

# Run main function
main "$@"
