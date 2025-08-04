#!/bin/bash

# Development startup script for Werewolf AI Game
# This script starts the development environment with hot reloading

echo "🐺 Starting Werewolf AI Game Development Environment"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please update it with your credentials."
    else
        echo "❌ .env.example file not found. Please create .env file manually."
        exit 1
    fi
fi

# Function to cleanup on exit
cleanup() {
    echo "🛑 Stopping development environment..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Start development environment
echo "🚀 Starting services with hot reloading..."
echo ""
echo "Backend will be available at: http://localhost:8000"
echo "Frontend will be available at: http://localhost:3000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Start with development overrides
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Cleanup will be called automatically by the trap
