#!/bin/bash
#
# Download models for Slovenian ASR pipeline.
#
# This script downloads:
#   1. PROTOVERB-ASR-E2E 1.0 - Slovenian ASR model (~431MB)
#   2. RSDO-DS2-P&C 3.6 - Punctuation & Capitalization model (~388MB)
#   3. Slovene_denormalizator - Text denormalization (git clone)
#
# Usage:
#   ./download_models.sh
#
# After running, you should have:
#   models/asr/conformer_ctc_bpe.nemo
#   models/punctuator/nlp_tc_pc.nemo
#   Slovene_denormalizator/
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo " Slovenian ASR Pipeline - Model Setup"
echo "========================================"
echo ""

# Check for required tools
for cmd in curl zstd tar git; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: $cmd is required but not installed."
        exit 1
    fi
done

# 1. ASR Model (PROTOVERB-ASR-E2E 1.0)
echo "[1/3] Downloading ASR model (PROTOVERB-ASR-E2E 1.0)..."
echo "      Size: ~431MB"
echo ""

mkdir -p models/asr
cd models/asr

if [ -f "conformer_ctc_bpe.nemo" ]; then
    echo "      Already exists, skipping."
else
    echo "      Downloading..."
    curl -L -o sl-SI_MOL_nemo-1.0.tar.zst \
        "https://www.clarin.si/repository/xmlui/bitstream/handle/11356/2024/sl-SI_MOL_nemo-1.0.tar.zst?sequence=1&isAllowed=y"

    echo "      Extracting..."
    zstd -d sl-SI_MOL_nemo-1.0.tar.zst
    tar -xf sl-SI_MOL_nemo-1.0.tar

    # Find and move the model file (handles both naming conventions)
    find . -name "conformer*.nemo" -exec mv {} conformer_ctc_bpe.nemo \;

    # Cleanup
    rm -rf v* sl-SI_MOL_nemo-1.0.tar* 2>/dev/null || true

    echo "      Done!"
fi

cd "$SCRIPT_DIR"

# 2. Punctuator Model (RSDO-DS2-P&C 3.6)
echo ""
echo "[2/3] Downloading Punctuator model (RSDO-DS2-P&C 3.6)..."
echo "      Size: ~388MB"
echo ""

mkdir -p models/punctuator
cd models/punctuator

if [ -f "nlp_tc_pc.nemo" ]; then
    echo "      Already exists, skipping."
else
    echo "      Downloading..."
    curl -L -o sl-SI_GEN_nemo-3.6.tar.zst \
        "https://www.clarin.si/repository/xmlui/bitstream/handle/11356/1735/sl-SI_GEN_nemo-3.6.tar.zst?sequence=3&isAllowed=y"

    echo "      Extracting..."
    zstd -d sl-SI_GEN_nemo-3.6.tar.zst
    tar -xf sl-SI_GEN_nemo-3.6.tar

    # Find and move the model file
    find . -name "nlp_tc_pc.nemo" -exec mv {} . \;

    # Cleanup
    rm -rf v* sl-SI_GEN_nemo-3.6.tar* 2>/dev/null || true

    echo "      Done!"
fi

cd "$SCRIPT_DIR"

# 3. Denormalizer (Slovene_denormalizator)
echo ""
echo "[3/3] Cloning Slovene_denormalizator..."
echo ""

if [ -d "Slovene_denormalizator" ]; then
    echo "      Already exists, updating..."
    cd Slovene_denormalizator
    git pull || true
    cd "$SCRIPT_DIR"
else
    git clone https://github.com/clarinsi/Slovene_denormalizator.git
fi

echo "      Done!"

# Summary
echo ""
echo "========================================"
echo " Setup Complete!"
echo "========================================"
echo ""
echo " Models downloaded:"
echo "   - models/asr/conformer_ctc_bpe.nemo"
echo "   - models/punctuator/nlp_tc_pc.nemo"
echo "   - Slovene_denormalizator/"
echo ""
echo " Total size: ~820MB"
echo ""
echo " Next steps:"
echo "   1. Build Docker image:"
echo "      docker build -t slovene-asr-local ."
echo ""
echo "   2. Test locally:"
echo "      docker run --rm -v \$(pwd)/test_audio.wav:/app/test_audio.wav \\"
echo "        slovene-asr-local python test_local.py /app/test_audio.wav"
echo ""
