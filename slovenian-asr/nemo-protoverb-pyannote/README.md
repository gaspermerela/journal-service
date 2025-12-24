# RunPod Slovenian ASR with pyannote Diarization

Serverless handler for Slovenian ASR with speaker diarization using **pyannote** (replaces NeMo ClusteringDiarizer).

## Key Differences from nemo-protoverb-nfa

| Component | nemo-protoverb-nfa | This variant (pyannote) |
|-----------|-------------------|-------------------------|
| Diarization | NeMo ClusteringDiarizer | pyannote 3.1 |
| VAD | MarbleNet | pyannote's PyanNet |
| Speaker embeddings | TitaNet-Large | pyannote's WeSpeaker |
| Segments (30-min audio) | ~1200 | ~120 (10x fewer) |
| Overlap detection | Basic | Superior |
| License | Apache 2.0 | MIT |

**Why pyannote?** Produces fewer, longer segments → reduces short segment ASR degradation.

## Pipeline

```
Audio
  ↓
pyannote speaker-diarization-3.1  (replaces NeMo diarization)
  ↓
Speaker segments [{start, duration, speaker}, ...]
  ↓
Pre-merge short segments (<3s same-speaker)
  ↓
Process in parallel:
  ├─ Extract audio segment (with 0.5s padding)
  ├─ PROTOVERB ASR → text
  └─ NFA (aligner_utils.py) → word timestamps
  ↓
Merge consecutive same-speaker turns
  ↓
Punctuation + Denormalization
```

**Models:**
- [PROTOVERB-ASR-E2E 1.0](https://clarin.si/repository/xmlui/handle/11356/2024) - Slovenian ASR (9.8% WER improvement over RSDO 2.0)
- [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1) - Speaker diarization (MIT license)
- [RSDO-DS2-P&C](https://www.clarin.si/repository/xmlui/handle/11356/1735) - Punctuation & capitalization
- [Slovene_denormalizator](https://github.com/clarinsi/Slovene_denormalizator) - Numbers, dates, times
- NFA via `nemo_compat/aligner_utils.py` - Word-level timestamps (Viterbi alignment)

## Quick Start

### 1. Download Models

```bash
cd slovenian-asr/nemo-protoverb-pyannote
./download_models.sh
```

Or manually - see [Dockerfile](./Dockerfile) for URLs.

### 2. Get HuggingFace Token (Build Time Only)

pyannote models are gated and require authentication **at build time**:

1. Create account at https://huggingface.co
2. Accept terms at https://huggingface.co/pyannote/speaker-diarization-3.1
3. Accept terms at https://huggingface.co/pyannote/segmentation-3.0
4. Create token at https://huggingface.co/settings/tokens

**Note:** Token is only needed during `docker build`. Models are baked into the image for offline runtime.

### 3. Build Docker Image

```bash
# For RunPod (from slovenian-asr/nemo-protoverb-pyannote/ directory)
docker buildx build --platform linux/amd64 \
  --build-arg HF_TOKEN=hf_your_token_here \
  -t your-dockerhub/slovene-asr-pyannote:v1.0 --push .

# For local testing on M1/M2 Mac
docker build --build-arg HF_TOKEN=hf_your_token_here \
  -t slovene-asr-pyannote .
```

### 4. Local Testing

No HF_TOKEN needed at runtime - models are loaded from local paths baked into the image.

```bash
# Full pipeline with diarization
docker run --rm -v $(pwd)/test_audio.wav:/app/test_audio.wav \
  slovene-asr-pyannote python test_local.py /app/test_audio.wav --diarize

# ASR only (no diarization)
docker run --rm -v $(pwd)/test_audio.wav:/app/test_audio.wav \
  slovene-asr-pyannote python test_local.py /app/test_audio.wav --asr-only
```

### 5. Deploy to RunPod

1. Go to [RunPod Serverless](https://www.runpod.io/console/serverless)
2. Create endpoint with your Docker image
3. Configure: L4 GPU, EU-RO-1 region, 60s idle timeout

No environment variables required - all models are baked into the image.

## API

### Input

```json
{
  "input": {
    "audio_base64": "<base64 WAV>",
    "punctuate": true,
    "denormalize": true,
    "denormalize_style": "default",
    "enable_diarization": true,
    "speaker_count": null,
    "max_speakers": 10
  }
}
```

### Output (with diarization)

```json
{
  "text": "Speaker 1: Pozdravljeni. Speaker 2: Hvala.",
  "raw_text": "pozdravljeni hvala",
  "processing_time": 15.2,
  "pipeline": ["asr", "align", "diarize", "punctuate", "denormalize"],
  "model_version": "protoverb-1.0-pyannote",
  "diarization_applied": true,
  "word_level_timestamps": true,
  "speaker_count_detected": 2,
  "segments": [
    {
      "id": 0, "start": 0.32, "end": 1.5,
      "text": "Pozdravljeni.", "speaker": "Speaker 1",
      "words": [{"word": "Pozdravljeni.", "start": 0.32, "end": 1.5}]
    },
    {
      "id": 1, "start": 1.8, "end": 3.2,
      "text": "Hvala.", "speaker": "Speaker 2",
      "words": [{"word": "Hvala.", "start": 1.8, "end": 3.2}]
    }
  ]
}
```

## Files

| File | Description |
|------|-------------|
| `handler.py` | RunPod serverless handler (pyannote diarization) |
| `test_local.py` | CLI for local testing |
| `download_models.sh` | Download ASR/punctuator models |
| `Dockerfile` | Container with pyannote + NeMo ASR |
| `nemo_compat/` | NFA word alignment (aligner_utils.py from NeMo 2.x) |

## Audio Requirements

- Format: WAV (16-bit PCM)
- Sample rate: 16kHz
- Channels: Mono

## Comparison with nemo-protoverb-nfa

For A/B testing, compare results between:
- `nemo-protoverb-nfa/` - NeMo ClusteringDiarizer (more segments, faster)
- `nemo-protoverb-pyannote/` - pyannote 3.1 (fewer segments, better overlap handling)
