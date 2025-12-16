# Docker Initialization Script for NINA Guardrail Monitor
# This script sets up and starts all services using Docker Compose

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NINA Guardrail Monitor - Docker Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "[1/5] Checking Docker..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
Write-Host "[2/5] Checking Docker Compose..." -ForegroundColor Yellow
try {
    docker compose version | Out-Null
    Write-Host "✅ Docker Compose is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose is not available. Please install Docker Compose." -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
Write-Host "[3/5] Checking environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env" -ErrorAction SilentlyContinue
    if (-not (Test-Path ".env")) {
        Write-Host "⚠️  .env.example not found. You may need to configure environment variables manually." -ForegroundColor Yellow
    } else {
        Write-Host "✅ Created .env file. Please review and update with your settings." -ForegroundColor Green
    }
} else {
    Write-Host "✅ .env file exists" -ForegroundColor Green
}

# Build and start services
Write-Host "[4/5] Building Docker images..." -ForegroundColor Yellow
docker compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to build Docker images" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker images built successfully" -ForegroundColor Green

# Start services
Write-Host "[5/5] Starting services..." -ForegroundColor Yellow
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start services" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ All services started successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services are now running:" -ForegroundColor Cyan
Write-Host "  • Guardrail-Strategy:  http://localhost:5001" -ForegroundColor White
Write-Host "  • OFH Dashboard API:   http://localhost:5000" -ForegroundColor White
Write-Host "  • OFH Dashboard UI:    http://localhost:3001" -ForegroundColor White
Write-Host "  • Kafka:               localhost:9092" -ForegroundColor White
Write-Host "  • PostgreSQL:          localhost:5432" -ForegroundColor White
Write-Host "  • Redis:               localhost:6379" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  • View logs:           docker compose logs -f" -ForegroundColor White
Write-Host "  • Stop services:        docker compose down" -ForegroundColor White
Write-Host "  • Restart services:     docker compose restart" -ForegroundColor White
Write-Host "  • View status:          docker compose ps" -ForegroundColor White
Write-Host ""
Write-Host "To view logs for a specific service:" -ForegroundColor Cyan
Write-Host "  docker compose logs -f guardrail-strategy" -ForegroundColor White
Write-Host "  docker compose logs -f ofh-dashboard-backend" -ForegroundColor White
Write-Host "  docker compose logs -f kafka" -ForegroundColor White
Write-Host ""

