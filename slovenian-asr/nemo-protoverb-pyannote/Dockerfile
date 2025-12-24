# RunPod Serverless Container for Slovenian ASR with pyannote Diarization
#
# This Dockerfile creates a container that runs the PROTOVERB NeMo model
# for Slovenian speech-to-text with optional punctuation, denormalization,
# and speaker diarization using pyannote (instead of NeMo ClusteringDiarizer).
#
# Pipeline:
#   Without diarization: Audio -> ASR -> Punctuation -> Denormalization
#   With diarization: Audio -> pyannote -> ASR + NFA per segment -> Merge -> Punct -> Denorm
#
# Build for RunPod (from slovenian-asr/nemo-protoverb-pyannote/ directory):
#   docker buildx build --platform linux/amd64 \
#     --build-arg HF_TOKEN=hf_your_token_here \
#     -t YOUR_DOCKERHUB/slovene-asr-pyannote:v1.0 --push .
#
# Build for local testing (M1/M2 Mac):
#   docker build --build-arg HF_TOKEN=hf_your_token_here -t slovene-asr-pyannote .
#
# Local test (no HF_TOKEN needed at runtime - models are baked in):
#   docker run --rm -v $(pwd)/test_audio.wav:/app/test_audio.wav \
#     slovene-asr-pyannote python test_local.py /app/test_audio.wav --diarize
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
#
#   4. pyannote models (gated - requires HuggingFace token):
#      Accept terms at: https://hf.co/pyannote/speaker-diarization-3.1
#      Accept terms at: https://hf.co/pyannote/segmentation-3.0

FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# HuggingFace token for pyannote model download (gated model)
# Only needed at build time - models are cached in image
# NOTE: Token visible in image history - use private registry or accept risk
ARG HF_TOKEN

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

# pyannote for speaker diarization (replaces NeMo ClusteringDiarizer)
# Downgrade numpy<2 first - pyannote.audio 3.1.1 uses np.NaN (removed in NumPy 2.0)
# Force reinstall numpy to ensure downgrade takes effect
RUN pip install --no-cache-dir --force-reinstall "numpy<2" && \
    pip install --no-cache-dir pyannote.audio==3.1.1

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
# Re-pin numpy<2 after because denormalizer may upgrade it
RUN pip install --no-cache-dir -r /app/Slovene_denormalizator/requirements.txt || true && \
    pip install --no-cache-dir "numpy<2"

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

# Pre-download pyannote models for OFFLINE usage (no HF_TOKEN needed at runtime)
# Requires HF_TOKEN at BUILD time with accepted terms for:
#   - pyannote/speaker-diarization-3.1
#   - pyannote/segmentation-3.0
#
# Downloads model files and creates local config.yaml for offline loading.
# See: https://github.com/pyannote/pyannote-audio/blob/develop/tutorials/community/offline_usage_speaker_diarization.ipynb
RUN mkdir -p /app/models/pyannote && \
    python -c "import os; from huggingface_hub import hf_hub_download; token='${HF_TOKEN}'; \
seg=hf_hub_download('pyannote/segmentation-3.0','pytorch_model.bin',use_auth_token=token); \
os.system(f'cp {seg} /app/models/pyannote/segmentation-3.0.bin'); \
emb=hf_hub_download('pyannote/wespeaker-voxceleb-resnet34-LM','pytorch_model.bin',use_auth_token=token); \
os.system(f'cp {emb} /app/models/pyannote/wespeaker-voxceleb-resnet34-LM.bin'); \
cfg=hf_hub_download('pyannote/speaker-diarization-3.1','config.yaml',use_auth_token=token); \
os.system(f'cp {cfg} /app/models/pyannote/config.yaml'); \
print('Downloaded pyannote models')"

# Patch the config.yaml to use local model paths
RUN python -c "import yaml; \
f=open('/app/models/pyannote/config.yaml'); c=yaml.safe_load(f); f.close(); \
c['pipeline']['params']['segmentation']='/app/models/pyannote/segmentation-3.0.bin'; \
c['pipeline']['params']['embedding']='/app/models/pyannote/wespeaker-voxceleb-resnet34-LM.bin'; \
f=open('/app/models/pyannote/config.yaml','w'); yaml.dump(c,f); f.close(); \
print('Patched config.yaml'); print(open('/app/models/pyannote/config.yaml').read())"

# NFA (Forced Alignment) reuses PROTOVERB model via NeMo aligner_utils
# No separate model download needed (saves ~2GB vs MMS approach)

# =============================================================================
# LAYER 5: Application code (changes frequently - LAST for best caching)
# =============================================================================
COPY handler.py /app/
COPY test_local.py /app/

# NeMo 2.x compatibility module (aligner_utils.py for Viterbi word timestamps)
COPY nemo_compat /app/nemo_compat

# =============================================================================
# Environment and entrypoint
# =============================================================================
ENV ASR_MODEL_PATH=/app/models/asr/conformer_ctc_bpe.nemo
ENV PUNCTUATOR_MODEL_PATH=/app/models/punctuator/nlp_tc_pc.nemo
ENV DENORMALIZER_PATH=/app/Slovene_denormalizator
ENV PYANNOTE_CONFIG_PATH=/app/models/pyannote/config.yaml
ENV NVIDIA_VISIBLE_DEVICES=all
ENV PYTHONUNBUFFERED=1

# RunPod uses this as entry point
CMD ["python", "-u", "handler.py"]
