# RunPod Serverless Container for RSDO Slovenian ASR
#
# This Dockerfile creates a container that runs the RSDO NeMo model
# for Slovenian speech-to-text on RunPod serverless GPU.
#
# Build (from runpod/ directory):
#   docker buildx build --platform linux/amd64 -t YOUR_DOCKERHUB/rsdo-slovenian-asr:latest --push .
#
# Prerequisites:
#   1. Download model archive:
#      curl -L -o models/sl-SI_GEN_nemo-2.0.tar.zst "https://www.clarin.si/repository/xmlui/bitstream/handle/11356/1737/sl-SI_GEN_nemo-2.0.tar.zst"
#   2. Extract:
#      cd models && zstd -d sl-SI_GEN_nemo-2.0.tar.zst && tar -xf sl-SI_GEN_nemo-2.0.tar
#   3. Move model file:
#      mv v2.0/conformer_ctc_bpe.nemo . && rm -rf v2.0 sl-SI_GEN_nemo-2.0.tar*

FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Cython must be installed first for NeMo dependencies
RUN pip install --no-cache-dir Cython

# Note: nemo_toolkit[asr] includes all necessary ASR dependencies
# huggingface_hub<0.24 required for NeMo 1.21 (ModelFilter was removed in 0.24)
RUN pip install --no-cache-dir \
    "huggingface_hub<0.24" \
    nemo_toolkit[asr]==1.21.0 \
    runpod>=1.6.0 \
    soundfile>=0.12.1

# Copy handler code
COPY handler.py /app/

# Copy RSDO model (must be downloaded first)
# The model file is ~430MB
COPY models/conformer_ctc_bpe.nemo /app/models/

# Set environment variables
ENV MODEL_PATH=/app/models/conformer_ctc_bpe.nemo
ENV NVIDIA_VISIBLE_DEVICES=all
ENV PYTHONUNBUFFERED=1

# RunPod uses this as entry point
CMD ["python", "-u", "handler.py"]
