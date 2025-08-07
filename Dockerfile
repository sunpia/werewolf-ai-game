# Build stage
FROM python:3.13-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM builder AS development

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 werewolf && chown -R werewolf:werewolf /app
USER werewolf

# Expose port
EXPOSE 8000

# Run the application with reload for development
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

# Production stage
FROM python:3.13-slim AS production

# Set working directory
WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder stage
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY app.py .
COPY main.py .

# Create non-root user with specific UID for security
RUN useradd -m -u 1000 werewolf && chown -R werewolf:werewolf /app
USER werewolf

# Set environment variables for production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000
# Run the application with optimized settings for production
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
