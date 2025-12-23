# RunPod Slovenian ASR with NLP Pipeline

Serverless handler for Slovenian ASR with punctuation and denormalization on RunPod GPU.

## Pipeline

```
Audio -> ASR (PROTOVERB) -> Punctuation -> Denormalization
         |                       |                |
         v                       v                v
"včeraj sem spal        "Včeraj sem spal    "Včeraj sem spal
 osem ur in pol"         osem ur in pol."     8,5 ure."
```

**Models:**
- [PROTOVERB-ASR-E2E 1.0](https://clarin.si/repository/xmlui/handle/11356/2024) - 9.8% WER improvement over RSDO 2.0
- [RSDO-DS2-P&C](https://www.clarin.si/repository/xmlui/handle/11356/1735) - Punctuation & capitalization
- [Slovene_denormalizator](https://github.com/clarinsi/Slovene_denormalizator) - Numbers, dates, times

## Quick Start

### 1. Download Models

```bash
cd slovenian-asr/nemo-protoverb
./download_models.sh
```

Or manually - see [Dockerfile](./Dockerfile) for URLs.

### 2. Build Docker Image

```bash
# For RunPod (from slovenian-asr/nemo-protoverb/ directory)
docker buildx build --platform linux/amd64 \
  -t your-dockerhub/slovene-asr-pipeline:v2.0 --push .

# For local testing on M1/M2 Mac
docker build -t slovene-asr-local .
```

### 3. Local Testing

```bash
# Full pipeline
docker run --rm -v $(pwd)/test_audio.wav:/app/test_audio.wav \
  slovene-asr-local python test_local.py /app/test_audio.wav

# ASR only (no punctuation/denormalization)
docker run --rm -v $(pwd)/test_audio.wav:/app/test_audio.wav \
  slovene-asr-local python test_local.py /app/test_audio.wav --asr-only

# Compare all modes
docker run --rm -v $(pwd)/test_audio.wav:/app/test_audio.wav \
  slovene-asr-local python test_local.py /app/test_audio.wav --compare
```

### 4. Deploy to RunPod

1. Go to [RunPod Serverless](https://www.runpod.io/console/serverless)
2. Create endpoint with your Docker image
3. Configure: L4 GPU, EU-RO-1 region, 60s idle timeout

## API

### Input

```json
{
  "input": {
    "audio_base64": "<base64 WAV>",
    "punctuate": true,
    "denormalize": true,
    "denormalize_style": "default"
  }
}
```

### Output

```json
{
  "text": "Včeraj sem spal 8 ur.",
  "raw_text": "včeraj sem spal osem ur",
  "processing_time": 3.5,
  "pipeline": ["asr", "punctuate", "denormalize"],
  "model_version": "protoverb-1.0"
}
```

## Files

| File | Description |
|------|-------------|
| `handler.py` | RunPod serverless handler |
| `test_local.py` | CLI for local testing |
| `download_models.sh` | Download all models |
| `Dockerfile` | Container with optimized layer caching |

## Audio Requirements

- Format: WAV (16-bit PCM)
- Sample rate: 16kHz
- Channels: Mono