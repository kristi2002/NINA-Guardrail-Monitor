# Docker Setup Guide for NINA Guardrail Monitor

This guide explains how to set up and run the entire NINA Guardrail Monitor system using Docker Compose.

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** (Windows/Mac) or **Docker Engine + Docker Compose** (Linux)
- **Git** (to clone the repository)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd "NINA Guardrail-Monitor"
```

### 2. Initialize and Start Services

#### Windows (PowerShell)

```powershell
.\docker-init.ps1
```

#### Linux/Mac (Bash)

```bash
chmod +x docker-init.sh
./docker-init.sh
```

#### Manual Setup

If you prefer to run commands manually:

```bash
# Build all Docker images
docker compose build

# Start all services
docker compose up -d

# View logs
docker compose logs -f
```

### 3. Access the Services

Once all services are running, you can access:

- **Guardrail-Strategy API**: http://localhost:5001
- **OFH Dashboard API**: http://localhost:5000
- **OFH Dashboard UI**: http://localhost:3001
- **Kafka**: localhost:9092
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 📋 Services Overview

The Docker Compose setup includes:

1. **Zookeeper** - Required for Kafka coordination
2. **Kafka** - Message queue for async communication
3. **PostgreSQL** - Database for OFH Dashboard
4. **Redis** - Caching and rate limiting
5. **Guardrail-Strategy** - Message validation service
6. **OFH Dashboard Backend** - Flask API server
7. **OFH Dashboard Frontend** - React frontend (served via Nginx)

## 🔧 Configuration

### Environment Variables

The services use environment variables for configuration. You can:

1. **Use default values** - Services will start with sensible defaults
2. **Create a `.env` file** - Place it in the root directory
3. **Override in docker-compose.yml** - Edit the environment section

### Key Environment Variables

#### Guardrail-Strategy

```env
KAFKA_BOOTSTRAP_SERVERS=kafka:9093  # Use Docker service name
OPENAI_API_KEY=your-key-here        # Optional, for LLM context checks
GUARDRAIL_ENABLE_PII_DETECTION=True
GUARDRAIL_ENABLE_TOXICITY_CHECK=True
```

#### OFH Dashboard Backend

```env
DATABASE_URL=postgresql://nina_user:nina_pass@postgres:5432/nina_db
KAFKA_BOOTSTRAP_SERVERS=kafka:9093  # Use Docker service name
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
ADMIN_PASSWORD=admin123
```

**Note**: Inside Docker containers, services communicate using Docker service names (e.g., `kafka:9093`). From your host machine, use `localhost:9092` for Kafka.

## 🛠️ Common Commands

### View Service Status

```bash
docker compose ps
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f guardrail-strategy
docker compose logs -f ofh-dashboard-backend
docker compose logs -f kafka
```

### Stop Services

```bash
docker compose down
```

### Stop and Remove Volumes

```bash
docker compose down -v
```

**Warning**: This will delete all database data!

### Restart a Specific Service

```bash
docker compose restart guardrail-strategy
docker compose restart ofh-dashboard-backend
```

### Rebuild After Code Changes

```bash
# Rebuild specific service
docker compose build guardrail-strategy
docker compose up -d guardrail-strategy

# Rebuild all services
docker compose build
docker compose up -d
```

## 🔍 Troubleshooting

### Services Won't Start

1. **Check Docker is running**:
   ```bash
   docker info
   ```

2. **Check port conflicts**:
   - Ensure ports 5000, 5001, 3001, 9092, 5432, 6379, 2181 are not in use
   - On Windows, check with: `netstat -ano | findstr :5000`

3. **Check logs**:
   ```bash
   docker compose logs
   ```

### Kafka Connection Issues

If services can't connect to Kafka:

1. **Wait for Kafka to be healthy**:
   ```bash
   docker compose ps kafka
   ```
   Kafka takes ~60 seconds to start.

2. **Check Kafka is accessible**:
   ```bash
   docker compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092
   ```

3. **Verify network connectivity**:
   ```bash
   docker compose exec guardrail-strategy ping kafka
   ```

### Database Connection Issues

1. **Wait for PostgreSQL to be healthy**:
   ```bash
   docker compose ps postgres
   ```

2. **Check database logs**:
   ```bash
   docker compose logs postgres
   ```

3. **Verify connection from backend**:
   ```bash
   docker compose exec ofh-dashboard-backend python -c "from core.database import init_database; init_database('postgresql://nina_user:nina_pass@postgres:5432/nina_db')"
   ```

### Frontend Can't Connect to Backend

1. **Check backend is running**:
   ```bash
   docker compose ps ofh-dashboard-backend
   ```

2. **Check backend logs**:
   ```bash
   docker compose logs ofh-dashboard-backend
   ```

3. **Verify API is accessible**:
   ```bash
   curl http://localhost:5000/api/health
   ```

### Reset Everything

If you need to start fresh:

```bash
# Stop all services and remove containers
docker compose down

# Remove volumes (deletes all data)
docker compose down -v

# Remove images (optional)
docker compose down --rmi all

# Start fresh
docker compose build
docker compose up -d
```

## 📊 Monitoring

### Check Service Health

```bash
# All services
docker compose ps

# Specific service health
docker inspect nina-guardrail-strategy | grep -A 10 Health
```

### View Resource Usage

```bash
docker stats
```

## 🔄 Development Workflow

### Making Code Changes

1. **Edit code** in your local files
2. **Rebuild the affected service**:
   ```bash
   docker compose build guardrail-strategy
   docker compose up -d guardrail-strategy
   ```
3. **View logs** to verify changes:
   ```bash
   docker compose logs -f guardrail-strategy
   ```

### Running Tests

You can run tests inside containers:

```bash
# Guardrail-Strategy tests
docker compose exec guardrail-strategy python -m pytest

# OFH Dashboard backend tests
docker compose exec ofh-dashboard-backend python -m pytest
```

### Database Migrations

Run migrations inside the backend container:

```bash
docker compose exec ofh-dashboard-backend python init_database.py
```

## 🚢 Production Considerations

For production deployment:

1. **Set strong secrets** in `.env`:
   - `SECRET_KEY` (min 32 characters)
   - `JWT_SECRET_KEY` (min 32 characters)
   - `ADMIN_PASSWORD` (strong password)

2. **Configure CORS** properly:
   ```env
   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

3. **Use external Kafka cluster** (if needed):
   ```env
   KAFKA_BOOTSTRAP_SERVERS=your-kafka-cluster:9092
   ```

4. **Use external PostgreSQL** (if needed):
   ```env
   DATABASE_URL=postgresql://user:pass@your-db-host:5432/dbname
   ```

5. **Enable HTTPS** via reverse proxy (Nginx/Traefik)

6. **Set resource limits** in docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1'
         memory: 1G
   ```

## 📝 Notes

- **Kafka Topics**: Topics are auto-created on first use (`KAFKA_AUTO_CREATE_TOPICS_ENABLE=true`)
- **Database**: PostgreSQL data persists in Docker volume `postgres_data`
- **Redis**: Redis data persists in Docker volume `redis_data`
- **Logs**: Application logs are mounted to host directories for easy access
- **Networking**: All services communicate via Docker network `nina-network`

## 🆘 Getting Help

If you encounter issues:

1. Check the logs: `docker compose logs`
2. Verify service health: `docker compose ps`
3. Review this guide's troubleshooting section
4. Check the main README.md for additional information

---

**Last Updated**: November 2025

