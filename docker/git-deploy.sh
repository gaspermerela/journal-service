#!/bin/bash
################################################################################
# JOURNAL SERVICE - SIMPLIFIED DEPLOYMENT
################################################################################
# Simple git-based deployment script for Docker Compose V2
#
# Configuration:
#   Set PROJECT_DIR and BACKUP_DIR in .env file in project directory
#
# Usage:
#   ./docker/git-deploy-simple.sh [OPTIONS] [VERSION]
#
# Options:
#   --force         Skip uncommitted changes check
#   --no-backup     Skip database backup
#   --no-cache      Build Docker image without cache
#   --help          Show this help
#
# Examples:
#   ./docker/git-deploy-simple.sh              # Deploy current branch
#   ./docker/git-deploy-simple.sh v0.2.0       # Deploy specific tag
#   ./docker/git-deploy-simple.sh --force main # Force deploy main branch
################################################################################

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Parse flags
FORCE=false
NO_BACKUP=false
NO_CACHE=false
VERSION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --force) FORCE=true; shift ;;
        --no-backup) NO_BACKUP=true; shift ;;
        --no-cache) NO_CACHE=true; shift ;;
        --help)
            grep "^#" "$0" | sed 's/^# \?//'
            exit 0
            ;;
        -*) echo "Unknown option: $1"; exit 1 ;;
        *) VERSION="$1"; shift ;;
    esac
done

echo "========================================="
echo "Journal Service Deployment"
echo "========================================="
echo ""

# Auto-detect project directory from script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project directory
cd "$PROJECT_DIR" || {
    echo "Error: Cannot access project directory: $PROJECT_DIR"
    exit 1
}

# Load .env file from project directory
if [ ! -f .env ]; then
    echo "Error: .env file not found in $PROJECT_DIR"
    echo "Copy .env.example to .env and configure it"
    exit 1
fi

source .env

# Apply defaults if not set in .env
VERSION="${VERSION:-master}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"

echo "✓ Environment loaded from .env"
echo "Project directory: $(pwd)"
echo "Backup directory: $BACKUP_DIR"

# Check uncommitted changes
if [ "$FORCE" = false ] && [ -n "$(git status -s)" ]; then
    echo ""
    echo "Error: Uncommitted changes detected"
    git status -s
    echo ""
    echo "Use --force to deploy anyway"
    exit 1
fi

# Fetch and checkout
echo ""
echo "Fetching: $VERSION"
git fetch --all --tags --prune
git checkout "$VERSION"
git pull origin "$VERSION" 2>/dev/null || true

COMMIT=$(git rev-parse --short HEAD)
echo "✓ Checked out: $COMMIT"

# Backup database
if [ "$NO_BACKUP" = false ]; then
    echo ""
    echo "Creating backup..."
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/db_$(date +%Y%m%d_%H%M%S).sql"

    ERROR_FILE=$(mktemp)

    if PGPASSWORD="$DATABASE_PASSWORD" pg_dump -h "$DATABASE_HOST" -p "$DATABASE_PORT" -U "$DATABASE_USER" --schema=journal "$DATABASE_NAME" > "$BACKUP_FILE" 2>"$ERROR_FILE"; then
        echo "✓ Backup: $BACKUP_FILE"
        rm -f "$ERROR_FILE"
    else
        echo "Error: Database backup failed"
        cat "$ERROR_FILE"
        rm -f "$BACKUP_FILE" "$ERROR_FILE"
        exit 1
    fi
fi

# Build and deploy
echo ""
if [ "$NO_CACHE" = true ]; then
    echo "Building image without cache..."
    docker compose build --no-cache
else
    echo "Building image..."
    docker compose build
fi

echo ""
echo "Starting service..."
docker compose up -d --wait

# Verify health
echo ""
echo "Checking health..."
if curl -sf "http://localhost:${PORT:-8000}/health" > /dev/null; then
    echo "✓ Service is healthy"
else
    echo "! Health check failed (check logs)"
    docker compose logs --tail=20 app
    exit 1
fi

# Done
echo ""
echo "========================================="
echo "✓ Deployment Complete"
echo "========================================="
echo ""
echo "Deployed: $VERSION ($COMMIT)"
echo "Logs: docker compose logs -f app"
echo "Rollback: git checkout <previous-tag> && ./docker/git-deploy-simple.sh"
echo ""
