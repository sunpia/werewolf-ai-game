#!/bin/bash
set -e

# Configurable variables
USE_RANDOM_TAG=true  # Set to true to use a random tag
ENV="test"  # Set the environment (e.g., prod, staging)

# Get ECR repository URL from Terraform output
cd terraform
ECR_REPO_URL=$(terraform output -raw ecr_repository_url 2>/dev/null)
if [ -z "$ECR_REPO_URL" ]; then
    echo "❌ Could not get ECR repository URL from Terraform. Make sure Terraform is applied."
    exit 1
fi
cd ..

echo "📦 Using ECR Repository: $ECR_REPO_URL"

# Get tag
if [ "$USE_RANDOM_TAG" = true ]; then
    TAG=$(cat /dev/urandom | tr -dc 'a-z0-9' | fold -w 8 | head -n 1)
else
    TAG=$(git rev-parse --short HEAD)
fi

FULL_IMAGE="$ECR_REPO_URL:$TAG"

# Login to ECR
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin $ECR_REPO_URL

echo "Building Docker image: $FULL_IMAGE"
docker build -t "$FULL_IMAGE" . --target production
echo "Pushing Docker image: $FULL_IMAGE"
docker push "$FULL_IMAGE"

# Get the current task definition and filter out unwanted fields
aws ecs describe-task-definition --task-definition werewolf-${ENV}-backend \
    --query 'taskDefinition' \
    --output json | \
    jq 'del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' > task-def.json

# Update the image in the JSON
jq ".containerDefinitions[0].image = \"$FULL_IMAGE\"" task-def.json > updated-task-def.json

# Register new task definition
NEW_TASK_DEF_ARN=$(aws ecs register-task-definition --cli-input-json file://updated-task-def.json --query 'taskDefinition.taskDefinitionArn' --output text)

# Update the service to use the new task definition
aws ecs update-service \
    --cluster werewolf-${ENV}-cluster \
    --service werewolf-${ENV}-backend-service \
    --task-definition "$NEW_TASK_DEF_ARN" \
    --force-new-deployment

echo "Deployment complete. Service updated to use image: $FULL_IMAGE"