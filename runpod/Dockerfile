# RunPod Serverless Container for RSDO Slovenian ASR
#
# This Dockerfile creates a container that runs the RSDO NeMo model
# for Slovenian speech-to-text on RunPod serverless GPU.
#
# Build:
#   docker build -t your-registry/rsdo-slovenian-asr:latest -f runpod/Dockerfile .
#
# Prerequisites:
#   - Download RSDO model to models/ directory first (see scripts/download_rsdo_model.sh)

FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Note: nemo_toolkit[asr] includes all necessary ASR dependencies
RUN pip install --no-cache-dir \
    nemo_toolkit[asr]==1.21.0 \
    runpod>=1.6.0 \
    soundfile>=0.12.1

# Copy handler code
COPY runpod/handler.py /app/

# Copy RSDO model (must be downloaded first)
# The model file is ~430MB
COPY models/conformer_ctc_bpe.nemo /app/models/

# Set environment variables
ENV MODEL_PATH=/app/models/conformer_ctc_bpe.nemo
ENV NVIDIA_VISIBLE_DEVICES=all
ENV PYTHONUNBUFFERED=1

# RunPod uses this as entry point
CMD ["python", "-u", "handler.py"]
