#!/bin/bash

################################################################################
# JOURNAL SERVICE - SERVER DEPLOYMENT SCRIPT
################################################################################
#
# Purpose: Deploy a new version of journal-service on the server
#
# Workflow:
#   1. Validate environment (docker-compose.yml exists, docker running)
#   2. Load Docker image from tar file
#   3. Stop and remove old containers
#   4. Start new container using docker-compose
#   5. Wait for container to be healthy
#   6. Clean up old unused images
#
# Usage (on server):
#   ./run.sh v1.2.3     # Run specific version
#   ./run.sh            # Run latest available version
#
# This script is meant to be run ON THE SERVER, not locally.
#
################################################################################

set -e  # Exit immediately if any command fails

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
IMAGE_NAME="journal-service"
CONTAINER_STARTUP_TIMEOUT=30  # seconds to wait for container to be healthy

# -----------------------------------------------------------------------------
# Pre-flight checks - verify everything needed before starting
# -----------------------------------------------------------------------------
echo "Running pre-flight checks..."

# Check if Docker is running
if ! docker info &>/dev/null; then
  echo "Error: Docker is not running"
  echo "Start Docker and try again"
  exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
  echo "Error: docker-compose.yml not found in current directory"
  echo "Current directory: $(pwd)"
  echo ""
  echo "Make sure you're in the correct directory:"
  exit 1
fi

echo "✓ Pre-flight checks passed"
echo ""

# -----------------------------------------------------------------------------
# Parse version argument
# -----------------------------------------------------------------------------
VERSION="$1"

# If no version provided, find the latest tar file
if [ -z "$VERSION" ]; then
  echo "No version specified, searching for latest version..."

  # Find all tar files and extract versions
  LATEST_TAR=$(ls -t ${IMAGE_NAME}-*.tar 2>/dev/null | head -n 1)

  if [ -z "$LATEST_TAR" ]; then
    echo "Error: No tar files found for $IMAGE_NAME"
    echo "Usage: $0 <version>"
    exit 1
  fi

  # Extract version from filename (journal-service-v1.2.3.tar -> v1.2.3)
  # Remove prefix and suffix using bash parameter expansion
  VERSION="${LATEST_TAR#${IMAGE_NAME}-}"  # Remove "journal-service-" prefix
  VERSION="${VERSION%.tar}"                # Remove ".tar" suffix

  echo "Found latest version: $VERSION"
  echo "Press Enter to continue or Ctrl+C to cancel..."
  read
fi

# -----------------------------------------------------------------------------
# Verify tar file exists
# -----------------------------------------------------------------------------
TAR_FILE="${IMAGE_NAME}-${VERSION}.tar"

if [ ! -f "$TAR_FILE" ]; then
  echo "Error: Tar file not found: $TAR_FILE"
  echo ""
  echo "Available versions:"
  ls -1 ${IMAGE_NAME}-*.tar 2>/dev/null || echo "  (none)"
  exit 1
fi

echo ""
echo "===================================================================="
echo "Deploying journal-service"
echo "Version: $VERSION"
echo "Tar file: $TAR_FILE"
echo "===================================================================="
echo ""

# -----------------------------------------------------------------------------
# Step 1: Load Docker image from tar file
# -----------------------------------------------------------------------------
echo "Step 1/4: Loading Docker image from tar file..."
echo ""

docker load -i "$TAR_FILE"

# Tag the loaded image with our version
# (Docker load might use a different tag, so we normalize it)
docker tag "${IMAGE_NAME}:${VERSION}" "${IMAGE_NAME}:latest"

echo ""
echo "✓ Image loaded and tagged"
echo ""

# -----------------------------------------------------------------------------
# Step 2: Stop and remove old containers
# -----------------------------------------------------------------------------
echo "Step 2/4: Stopping old containers..."
echo ""

# Find all containers (running or stopped) with this name
OLD_CONTAINERS=$(docker ps -aq --filter "name=${IMAGE_NAME}")

if [ -n "$OLD_CONTAINERS" ]; then
  echo "Stopping containers..."
  docker stop $OLD_CONTAINERS || true

  echo "Removing containers..."
  docker rm $OLD_CONTAINERS || true

  echo "✓ Old containers removed"
else
  echo "No old containers found"
fi

echo ""

# -----------------------------------------------------------------------------
# Step 3: Start new container with docker-compose
# -----------------------------------------------------------------------------
echo "Step 3/4: Starting new container..."
echo ""

# Export VERSION so docker-compose can use it
export VERSION="$VERSION"

echo "Using docker-compose.yml"
docker compose up -d

echo ""
echo "✓ Container started"
echo ""

# -----------------------------------------------------------------------------
# Step 4: Wait for container to be healthy
# -----------------------------------------------------------------------------
echo "Step 4/5: Waiting for container to be healthy..."
echo ""

# Wait for container to be running and healthy
WAITED=0
while [ $WAITED -lt $CONTAINER_STARTUP_TIMEOUT ]; do
  # Check if container is running
  if docker ps --filter "name=${IMAGE_NAME}" --filter "status=running" --format '{{.Names}}' | grep -q "${IMAGE_NAME}"; then
    echo "✓ Container is running"

    # Give it a moment to fully initialize
    sleep 2

    # Try to check health endpoint (optional - continues even if this fails)
    if command -v curl &>/dev/null; then
      if curl -sf http://localhost:8000/health &>/dev/null; then
        echo "✓ Health check passed"
      else
        echo "! Health check endpoint not responding (this is OK, container is running)"
      fi
    fi

    break
  fi

  echo "Waiting for container to start... (${WAITED}s/${CONTAINER_STARTUP_TIMEOUT}s)"
  sleep 2
  WAITED=$((WAITED + 2))
done

if [ $WAITED -ge $CONTAINER_STARTUP_TIMEOUT ]; then
  echo "Warning: Container did not start within ${CONTAINER_STARTUP_TIMEOUT}s"
  echo "Check logs with: docker logs ${IMAGE_NAME}"
  echo ""
  echo "Continuing with cleanup anyway..."
fi

echo ""

# -----------------------------------------------------------------------------
# Step 5: Clean up old unused images
# -----------------------------------------------------------------------------
echo "Step 5/5: Cleaning up old images..."
echo ""

# Get images currently in use by running containers
USED_IMAGES=$(docker ps --format '{{.Image}}' | sort | uniq)

# Find all journal-service images
ALL_IMAGES=$(docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep "^${IMAGE_NAME}:" || true)

if [ -n "$ALL_IMAGES" ]; then
  echo "$ALL_IMAGES" | while read -r IMAGE_FULL IMAGE_ID; do
    # Skip if this image is currently in use
    if echo "$USED_IMAGES" | grep -q "$IMAGE_FULL"; then
      echo "Keeping $IMAGE_FULL (in use)"
      continue
    fi

    # Skip the current version
    if [[ "$IMAGE_FULL" == "${IMAGE_NAME}:${VERSION}" ]] || [[ "$IMAGE_FULL" == "${IMAGE_NAME}:latest" ]]; then
      echo "Keeping $IMAGE_FULL (current version)"
      continue
    fi

    # Remove old image
    echo "Removing old image: $IMAGE_FULL"
    docker rmi "$IMAGE_ID" 2>/dev/null || echo "  (Could not remove, might be in use)"
  done
else
  echo "No old images to clean up"
fi

echo ""

# -----------------------------------------------------------------------------
# Show container status and logs
# -----------------------------------------------------------------------------
echo "===================================================================="
echo "✓ Deployment complete!"
echo "===================================================================="
echo ""
echo "Container status:"
docker ps --filter "name=${IMAGE_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "Recent logs:"
echo "--------------------------------------------------------------------"
docker logs "${IMAGE_NAME}" --tail 20
echo "--------------------------------------------------------------------"
echo ""
echo "To view live logs: docker logs -f ${IMAGE_NAME}"
echo "To check health: curl http://localhost:8000/health"
echo ""
