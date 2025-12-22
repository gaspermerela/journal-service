# RunPod Serverless Container for Slovenian ASR with NLP Pipeline
#
# This Dockerfile creates a container that runs the PROTOVERB NeMo model
# for Slovenian speech-to-text with optional punctuation and denormalization.
#
# Pipeline: Audio -> ASR (PROTOVERB) -> Punctuation -> Denormalization
#
# Build for RunPod (from runpod/ directory):
#   docker buildx build --platform linux/amd64 -t YOUR_DOCKERHUB/slovene-asr-pipeline:v2.0 --push .
#
# Build for local testing (M1/M2 Mac):
#   docker build -t slovene-asr-local .
#
# Local test:
#   docker run --rm -v $(pwd)/test_audio.wav:/app/test_audio.wav \
#     slovene-asr-local python test_local.py /app/test_audio.wav
#
# Prerequisites - Download models:
#
#   1. ASR Model (PROTOVERB-ASR-E2E 1.0):
#      mkdir -p models/asr && cd models/asr
#      curl -L -o sl-SI_MOL_nemo-1.0.tar.zst "https://www.clarin.si/repository/xmlui/bitstream/handle/11356/2024/sl-SI_MOL_nemo-1.0.tar.zst"
#      zstd -d sl-SI_MOL_nemo-1.0.tar.zst && tar -xf sl-SI_MOL_nemo-1.0.tar
#      mv */conformer_ctc_bpe.nemo . && rm -rf v* sl-SI_MOL_nemo-1.0.tar*
#      cd ../..
#
#   2. Punctuator Model (RSDO-DS2-P&C):
#      mkdir -p models/punctuator && cd models/punctuator
#      curl -L -o sl-SI_GEN_nemo-3.6.tar.zst "https://www.clarin.si/repository/xmlui/bitstream/handle/11356/1735/sl-SI_GEN_nemo-3.6.tar.zst?sequence=3&isAllowed=y"
#      zstd -d sl-SI_GEN_nemo-3.6.tar.zst && tar -xf sl-SI_GEN_nemo-3.6.tar
#      mv */nlp_tc_pc.nemo . && rm -rf v* sl-SI_GEN_nemo-3.6.tar*
#      cd ../..
#
#   3. Denormalizer (Python package):
#      git clone https://github.com/clarinsi/Slovene_denormalizator.git

FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

WORKDIR /app

# =============================================================================
# LAYER 1: System dependencies (rarely changes)
# =============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# LAYER 2: Python dependencies (rarely changes)
# =============================================================================
# Cython must be installed first for NeMo dependencies
RUN pip install --no-cache-dir Cython

# nemo_toolkit[all] includes ASR and NLP (for punctuation model)
# huggingface_hub<0.24 required for NeMo 1.21 (ModelFilter was removed in 0.24)
RUN pip install --no-cache-dir \
    "huggingface_hub<0.24" \
    "nemo_toolkit[all]==1.21.0" \
    runpod>=1.6.0 \
    soundfile>=0.12.1

# =============================================================================
# LAYER 3: Models and data (rarely changes, slow to transfer)
# =============================================================================
# Copy ASR model (PROTOVERB - ~431MB)
COPY models/asr/conformer_ctc_bpe.nemo /app/models/asr/

# Copy Punctuator model (~388MB)
COPY models/punctuator/nlp_tc_pc.nemo /app/models/punctuator/

# Copy Denormalizer package
COPY Slovene_denormalizator /app/Slovene_denormalizator

# Install denormalizer dependencies
RUN pip install --no-cache-dir -r /app/Slovene_denormalizator/requirements.txt || true

# =============================================================================
# LAYER 4: Pre-download external data (slow, but cached)
# =============================================================================
# Pre-download NLTK data required by denormalizer
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# Pre-download EMBEDDIA/sloberta model used by punctuator
# This prevents runtime downloads and ensures consistent cold starts on RunPod
RUN python -c "from transformers import AutoModel, AutoTokenizer; \
    AutoModel.from_pretrained('EMBEDDIA/sloberta'); \
    AutoTokenizer.from_pretrained('EMBEDDIA/sloberta')"

# =============================================================================
# LAYER 5: Application code (changes frequently - LAST for best caching)
# =============================================================================
COPY handler.py /app/
COPY test_local.py /app/

# =============================================================================
# Environment and entrypoint
# =============================================================================
ENV ASR_MODEL_PATH=/app/models/asr/conformer_ctc_bpe.nemo
ENV PUNCTUATOR_MODEL_PATH=/app/models/punctuator/nlp_tc_pc.nemo
ENV DENORMALIZER_PATH=/app/Slovene_denormalizator
ENV NVIDIA_VISIBLE_DEVICES=all
ENV PYTHONUNBUFFERED=1

# RunPod uses this as entry point
CMD ["python", "-u", "handler.py"]
