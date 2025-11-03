# 🐳 Docker Deployment Guide

This guide covers deploying the AI Journal Backend Service using Docker with an external PostgreSQL database.

## 📋 Prerequisites

- Docker with Docker Compose
- PostgreSQL running via systemctl

## 🚀 Quick Start

### 1. Prepare Environment

```bash
# Copy and edit environment file
cp .env.docker .env
```

### 2. Build and Run with Docker Compose

```bash
# Create data directory with correct permissions
mkdir -p ./data/audio
sudo chown -R 1000:1000 ./data/audio

# Build and start the service (migrations run automatically)
docker compose -f docker-compose.yml up -d
```

**Note:** Database migrations run automatically on container startup via `alembic upgrade head`.

### 4. Verify Deployment

```bash
# Check health endpoint
curl http://localhost:8000/health

# View API documentation
curl http://localhost:8000/docs
```

## 📝 Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_HOST` | localhost | PostgreSQL host |
| `DATABASE_PORT` | 5432 | PostgreSQL port |
| `DATABASE_NAME` | postgres | Database name |
| `DATABASE_USER` | journal_user | Database user |
| `DATABASE_PASSWORD` | - | Database password (set to generated password) |
| `HOST` | 127.0.0.1 | Application host (127.0.0.1 for localhost only) |
| `PORT` | 8000 | Application port |
| `LOG_LEVEL` | INFO | Logging level |
| `AUDIO_STORAGE_PATH` | /app/data/audio | Audio storage path |
| `MAX_FILE_SIZE_MB` | 100 | Max upload size |
| `CORS_ORIGINS` | * | Allowed origins |
| `WORKERS` | 1 | Uvicorn workers |
| `DB_POOL_SIZE` | 5 | Connection pool size |
| `DB_MAX_OVERFLOW` | 10 | Max overflow connections |
| `DEBUG` | false | Debug mode |
| `RELOAD` | false | Auto-reload on changes |

## 🚀 Simplified Development Deployment Pipeline

For deploying to a remote server, we provide simplified deployment scripts focused on **reliability and simplicity**.

### Prerequisites

1. **Create deployment configuration to change defaults:**
```bash
cp .deploy-config.example .deploy-config
nano .deploy-config
```

Edit the following settings:
- `SSH_KEY`: Path to your SSH private key
- `PLATFORM`: Target architecture (`linux/amd64` or `linux/arm64`)
- `SERVER_USER`: SSH user on your server
- `SERVER_DIR`: Deployment directory on server

2. **Set server IP environment variable:**
```bash
export SERVER_IP=your.server.ip.address
```

### Deployment Workflow

**Step 1: Build and Upload (Local Machine)**

```bash
# Use git tag for versioning
cd /path/to/journal-service
git tag v1.0.0
./docker/deploy.sh

# Or specify version manually
./docker/deploy.sh v1.0.0

# Build without cache (clean build)
./docker/deploy.sh v1.0.0 --no-cache
```

**Note**: Version is required - either provide it manually or have a git tag. The script will fail if neither exists.

This script will:
- Build the Docker image
- Save it as a .tar file
- Upload it to your server

**Step 2: Run on Server**

SSH to your server and run:

```bash
# Using settings from .deploy-config
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP
cd $SERVER_DIR

# Create docker-compose.yml that uses the uploaded image

# Run the uploaded version
./run.sh v1.0.0

# Or auto-detect latest version
./run.sh
```

This script will:
- Load the Docker image from tar file
- Stop and remove old containers
- Start new container using docker-compose
- Clean up old unused images