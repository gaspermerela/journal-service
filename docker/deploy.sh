#!/bin/bash

################################################################################
# JOURNAL SERVICE - LOCAL DEPLOYMENT SCRIPT
################################################################################
#
# Purpose: Build Docker image locally and upload it to remote server
#
# Workflow:
#   1. Extract version from alembic (or use provided version)
#   2. Build Docker image for ARM64 platform
#   3. Save image as .tar file
#   4. Upload tar file to server via rsync
#
# Usage:
#   ./deploy.sh              # Use latest git tag (fails if no tags exist)
#   ./deploy.sh v1.2.3       # Use specific version
#   ./deploy.sh --no-cache   # Build without cache (still needs version/tag)
#
################################################################################

set -e  # Exit immediately if any command fails

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
IMAGE_NAME="journal-service"
TMP_DIR="./docker/tmp"

# Load configuration from .deploy-config if it exists
if [ -f ".deploy-config" ]; then
  echo "Loading configuration from .deploy-config..."
  source .deploy-config
fi

# Set defaults for any missing configuration values
SSH_KEY="${SSH_KEY:-~/.ssh/id_rsa}"
PLATFORM="${PLATFORM:-linux/amd64}"
SERVER_USER="${SERVER_USER:-deploy}"
SERVER_DIR="${SERVER_DIR:-/home/deploy/journal-service}"

# -----------------------------------------------------------------------------
# Pre-flight checks - verify everything needed before starting
# -----------------------------------------------------------------------------
echo "Running pre-flight checks..."

# Check if Docker is running
if ! docker info &>/dev/null; then
  echo "Error: Docker is not running"
  echo "Start Docker Desktop/daemon and try again"
  exit 1
fi

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
  echo "Error: Dockerfile not found in current directory"
  echo "Current directory: $(pwd)"
  echo ""
  echo "Make sure you're in the project root:"
  exit 1
fi

# Check if rsync is available
if ! command -v rsync &>/dev/null; then
  echo "Error: rsync is not installed"
  exit 1
fi

echo "✓ Pre-flight checks passed"
echo ""

# -----------------------------------------------------------------------------
# Parse command line arguments
# -----------------------------------------------------------------------------
VERSION=""
NO_CACHE=""

for arg in "$@"; do
  case "$arg" in
    --no-cache)
      NO_CACHE="--no-cache"
      echo "Building without cache"
      ;;
    v*)
      VERSION="$arg"
      echo "Using provided version: $VERSION"
      ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage: $0 [version] [--no-cache]"
      exit 1
      ;;
  esac
done

# -----------------------------------------------------------------------------
# Determine version if not provided
# -----------------------------------------------------------------------------
if [ -z "$VERSION" ]; then
  # Try to get latest git tag
  VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

  if [ -z "$VERSION" ]; then
    echo "Error: No version specified and no git tags found"
    echo ""
    echo "Options:"
    echo "  1. Provide version manually:"
    echo "     ./deploy.sh v1.0.0"
    echo ""
    echo "  2. Create a git tag:"
    echo "     git tag v1.0.0"
    echo "     ./deploy.sh"
    exit 1
  fi

  echo "Using git tag version: $VERSION"
fi

# -----------------------------------------------------------------------------
# Verify server environment variable
# -----------------------------------------------------------------------------
if [ -z "$SERVER_IP" ]; then
  echo "Error: SERVER_IP environment variable not set"
  exit 1
fi

echo ""
echo "===================================================================="
echo "Building and uploading journal-service"
echo "Version: $VERSION"
echo "Platform: $PLATFORM"
echo "Server: $SERVER_IP"
echo "===================================================================="
echo ""

# -----------------------------------------------------------------------------
# Step 1: Build Docker image
# -----------------------------------------------------------------------------
echo "Step 1/4: Building Docker image..."
echo "Command: docker build -t $IMAGE_NAME:$VERSION --platform $PLATFORM $NO_CACHE ."
echo ""

docker build \
  -t "$IMAGE_NAME:$VERSION" \
  --platform "$PLATFORM" \
  $NO_CACHE \
  .

echo "✓ Image built successfully"
echo ""

# -----------------------------------------------------------------------------
# Step 2: Save image as tar file
# -----------------------------------------------------------------------------
echo "Step 2/4: Saving image to tar file..."
mkdir -p "$TMP_DIR"
TAR_FILE="$TMP_DIR/$IMAGE_NAME-$VERSION.tar"

docker save "$IMAGE_NAME:$VERSION" -o "$TAR_FILE"

echo "✓ Image saved to $TAR_FILE"
echo "  Size: $(du -h "$TAR_FILE" | cut -f1)"
echo ""

# -----------------------------------------------------------------------------
# Step 3: Create server directory if needed
# -----------------------------------------------------------------------------
echo "Step 3/4: Ensuring server directory exists..."

ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_IP" "mkdir -p $SERVER_DIR"

echo "✓ Server directory ready"
echo ""

# -----------------------------------------------------------------------------
# Step 4: Upload tar file to server
# -----------------------------------------------------------------------------
echo "Step 4/4: Uploading image to server..."
echo ""

rsync \
  -e "ssh -i $SSH_KEY" \
  -avz \
  --progress \
  "$TAR_FILE" \
  "$SERVER_USER@$SERVER_IP:$SERVER_DIR/"

echo ""
echo "✓ Upload complete"
echo ""

# -----------------------------------------------------------------------------
# Cleanup (optional - commented out to keep tar for debugging)
# -----------------------------------------------------------------------------
# echo "Cleaning up local tar file..."
# rm -f "$TAR_FILE"

# -----------------------------------------------------------------------------
# Success message with next steps
# -----------------------------------------------------------------------------
echo "===================================================================="
echo "✓ Deployment preparation complete!"
echo "===================================================================="
echo ""
echo "Image $IMAGE_NAME:$VERSION is ready on the server."
echo ""
echo "Next steps:"
echo "  1. SSH to server:"
echo "     ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP"
echo ""
echo "  2. Navigate to deployment directory:"
echo "     cd $SERVER_DIR"
echo ""
echo "  3. Run the service:"
echo "     ./run.sh $VERSION"
echo ""
echo "===================================================================="
