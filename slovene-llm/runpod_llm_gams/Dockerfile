# GaMS (Generative Model for Slovene) LLM Handler for RunPod Serverless
#
# Optimized for L4 24GB GPU ($0.684/hr on RunPod Flex)
# Model: cjvt/GaMS-9B-Instruct (~18GB)
#
# Build:
#   docker buildx build --platform linux/amd64 -t your-registry/gams-llm:v1.0 .
#
# Test locally:
#   docker run --gpus all -p 8000:8000 your-registry/gams-llm:v1.0

# Base image with PyTorch + CUDA support
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

WORKDIR /app

# ============================================================================
# Layer 1: System dependencies
# ============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Layer 2: Python dependencies (cached unless requirements.txt changes)
# ============================================================================
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Layer 3: Download GaMS model (baked into image for fast cold starts)
#
# This downloads ~18GB model at build time. The model is cached in the image,
# so cold starts only need to load from local disk, not download from HF.
# ============================================================================
ENV HF_HOME=/app/models
ENV GAMS_MODEL_PATH=/app/models/gams-9b-instruct

RUN python -c "\
from huggingface_hub import snapshot_download; \
snapshot_download(\
    'cjvt/GaMS-9B-Instruct', \
    local_dir='/app/models/gams-9b-instruct', \
    local_dir_use_symlinks=False \
)"

# ============================================================================
# Layer 4: Application code (changes most frequently)
# ============================================================================
COPY handler.py /app/

# ============================================================================
# Runtime configuration
# ============================================================================
ENV PYTHONUNBUFFERED=1
ENV GAMS_MODEL_ID=cjvt/GaMS-9B-Instruct
ENV GPU_MEMORY_UTILIZATION=0.90
ENV MAX_MODEL_LEN=4096

# RunPod serverless entry point
CMD ["python", "-u", "handler.py"]
