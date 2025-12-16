#!/bin/bash
# Docker Initialization Script for NINA Guardrail Monitor
# This script sets up and starts all services using Docker Compose

echo "========================================"
echo "NINA Guardrail Monitor - Docker Setup"
echo "========================================"
echo ""

# Check if Docker is running
echo "[1/5] Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi
echo "✅ Docker is running"

# Check if Docker Compose is available
echo "[2/5] Checking Docker Compose..."
if ! docker compose version > /dev/null 2>&1; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    exit 1
fi
echo "✅ Docker Compose is available"

# Create .env file if it doesn't exist
echo "[3/5] Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please review and update with your settings."
    else
        echo "⚠️  .env.example not found. You may need to configure environment variables manually."
    fi
else
    echo "✅ .env file exists"
fi

# Build and start services
echo "[4/5] Building Docker images..."
docker compose build
if [ $? -ne 0 ]; then
    echo "❌ Failed to build Docker images"
    exit 1
fi
echo "✅ Docker images built successfully"

# Start services
echo "[5/5] Starting services..."
docker compose up -d
if [ $? -ne 0 ]; then
    echo "❌ Failed to start services"
    exit 1
fi

echo ""
echo "========================================"
echo "✅ All services started successfully!"
echo "========================================"
echo ""
echo "Services are now running:"
echo "  • Guardrail-Strategy:  http://localhost:5001"
echo "  • OFH Dashboard API:   http://localhost:5000"
echo "  • OFH Dashboard UI:    http://localhost:3001"
echo "  • Kafka:               localhost:9092"
echo "  • PostgreSQL:          localhost:5432"
echo "  • Redis:               localhost:6379"
echo ""
echo "Useful commands:"
echo "  • View logs:           docker compose logs -f"
echo "  • Stop services:        docker compose down"
echo "  • Restart services:     docker compose restart"
echo "  • View status:          docker compose ps"
echo ""
echo "To view logs for a specific service:"
echo "  docker compose logs -f guardrail-strategy"
echo "  docker compose logs -f ofh-dashboard-backend"
echo "  docker compose logs -f kafka"
echo ""

