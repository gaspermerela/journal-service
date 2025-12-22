#!/bin/bash
#
# Download RSDO Slovenian ASR model from CLARIN.SI
#
# This script downloads the RSDO-DS2-ASR-E2E 2.0 model which is
# purpose-built for Slovenian with 5.58% WER.
#
# Model info: https://www.clarin.si/repository/xmlui/handle/11356/1737
#
# Usage:
#   ./scripts/download_rsdo_model.sh
#
# The model will be downloaded to: runpod/models/conformer_ctc_bpe.nemo

set -e

MODEL_DIR="./runpod/models"
MODEL_URL="https://www.clarin.si/repository/xmlui/bitstream/handle/11356/1737/sl-SI_GEN_nemo-2.0.tar.zst"
ARCHIVE_NAME="sl-SI_GEN_nemo-2.0.tar.zst"

echo "=== RSDO Slovenian ASR Model Download ==="
echo ""

# Check for required tools
# "command -v <tool>" returns 0 if command exists, 1 if not
# "&> /dev/null" silences all output (both stdout and stderr)
if ! command -v wget &> /dev/null; then
    echo "Error: wget is required but not installed."
    echo "Install with: brew install wget (macOS) or apt install wget (Linux)"
    exit 1
fi

if ! command -v zstd &> /dev/null; then
    echo "Error: zstd is required but not installed."
    echo "Install with: brew install zstd (macOS) or apt install zstd (Linux)"
    exit 1
fi

# Create models directory
mkdir -p "$MODEL_DIR"
cd "$MODEL_DIR"

# Check if model already exists
if [ -f "conformer_ctc_bpe.nemo" ]; then
    echo "Model already exists at $MODEL_DIR/conformer_ctc_bpe.nemo"
    echo "Delete it first if you want to re-download."
    exit 0
fi

echo "Downloading RSDO ASR model (~430MB)..."
echo "Source: $MODEL_URL"
echo ""
wget -O "$ARCHIVE_NAME" "$MODEL_URL"

# Extract .tar.zst archive
# --use-compress-program=unzstd  tells tar to use zstd for decompression
# -x extract, -v verbose, -f filename
echo ""
echo "Extracting model archive..."
tar --use-compress-program=unzstd -xvf "$ARCHIVE_NAME"

# Archive extracts to v2.0/ subdirectory - move model to current dir
if [ -f "v2.0/conformer_ctc_bpe.nemo" ]; then
    mv v2.0/conformer_ctc_bpe.nemo .
    rm -rf v2.0
fi

rm -f "$ARCHIVE_NAME"

if [ ! -f "conformer_ctc_bpe.nemo" ]; then
    echo ""
    echo "Error: Model file not found after extraction."
    echo "Expected: conformer_ctc_bpe.nemo"
    echo "Please check the archive contents."
    exit 1
fi

# Heredoc: writes everything between << EOF and EOF to model.info
cat > model.info << EOF
# RSDO Slovenian ASR Model
language_code: sl-SI
domain: general
version: 2.0
model_type: nemo:conformer:ctc:bpe
wer: 5.58%
source: https://www.clarin.si/repository/xmlui/handle/11356/1737
training_data: ARTUR corpus (630h Slovenian speech)
EOF

echo ""
echo "=== Download Complete ==="
echo ""
echo "Model file: $MODEL_DIR/conformer_ctc_bpe.nemo"
echo "Model info: $MODEL_DIR/model.info"
echo ""
echo "You can now build the RunPod Docker image:"
echo "  cd runpod"
echo "  docker buildx build --platform linux/amd64 -t your-registry/protoverb-slovenian-asr:latest --push ."
