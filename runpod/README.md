# RunPod Slovenian ASR with NLP Pipeline

This directory contains the serverless handler for running Slovenian ASR with punctuation and denormalization on RunPod GPU.

## Overview

The handler uses the [PROTOVERB-ASR-E2E 1.0](https://clarin.si/repository/xmlui/handle/11356/2024) model (9.8% WER improvement over RSDO 2.0) with optional:
- **Punctuation & Capitalization** - [RSDO-DS2-P&C](https://www.clarin.si/repository/xmlui/handle/11356/1735)
- **Text Denormalization** - [Slovene_denormalizator](https://github.com/clarinsi/Slovene_denormalizator)

### Pipeline

```
Audio -> ASR (PROTOVERB) -> Punctuation (optional) -> Denormalization (optional)
         |                        |                          |
         v                        v                          v
"včeraj sem spal     "Včeraj sem spal      "Včeraj sem spal
 osem ur in pol"      osem ur in pol."       8,5 ure."
```

## Files

- `handler.py` - RunPod serverless handler with NLP pipeline
- `Dockerfile` - Container image for RunPod
- `requirements.txt` - Python dependencies

## Setup

### 1. Download Models

From the `runpod/` directory:

```bash
# ASR Model (PROTOVERB-ASR-E2E 1.0) - ~431MB
mkdir -p models/asr && cd models/asr
curl -L -o sl-SI_MOL_nemo-1.0.tar.zst \
  "https://www.clarin.si/repository/xmlui/bitstream/handle/11356/2024/sl-SI_MOL_nemo-1.0.tar.zst"
zstd -d sl-SI_MOL_nemo-1.0.tar.zst && tar -xf sl-SI_MOL_nemo-1.0.tar
mv */conformer_ctc_bpe.nemo . && rm -rf v* sl-SI_MOL_nemo-1.0.tar*
cd ../..

# Punctuator Model (RSDO-DS2-P&C) - ~388MB
mkdir -p models/punctuator && cd models/punctuator
curl -L -o sl-SI_GEN_nemo-3.6.tar.zst \
  "https://www.clarin.si/repository/xmlui/bitstream/handle/11356/1735/sl-SI_GEN_nemo-3.6.tar.zst?sequence=3&isAllowed=y"
zstd -d sl-SI_GEN_nemo-3.6.tar.zst && tar -xf sl-SI_GEN_nemo-3.6.tar
mv */nlp_tc_pc.nemo . && rm -rf v* sl-SI_GEN_nemo-3.6.tar*
cd ../..

# Denormalizer (Python package)
git clone https://github.com/clarinsi/Slovene_denormalizator.git
```

### 2. Build and Push Docker Image

```bash
# From runpod/ directory
docker buildx build --platform linux/amd64 \
  -t your-dockerhub-username/slovene-asr-pipeline:v2.0 --push .
```

> **Note:** The `--platform linux/amd64` flag is required when building on Apple Silicon (M1/M2/M3) since RunPod uses x86 GPUs.

### 3. Create RunPod Serverless Endpoint

1. Go to [RunPod Serverless](https://www.runpod.io/console/serverless)
2. Click "New Endpoint"
3. Configure:
   - **Container Image**: `your-dockerhub-username/slovene-asr-pipeline:v2.0`
   - **GPU Type**: L4 (recommended) or T4
   - **Max Workers**: 3 (or as needed)
   - **Idle Timeout**: 60 seconds
   - **Execution Timeout**: 300 seconds (5 minutes)
   - **Region**: EU-RO-1 (Romania) for GDPR compliance
4. Copy the Endpoint ID

### 4. Configure Environment Variables

Add to your `.env`:

```bash
TRANSCRIPTION_PROVIDER=clarinsi_slovene_asr
RUNPOD_API_KEY=your_runpod_api_key
RUNPOD_ENDPOINT_ID=your_endpoint_id

# Optional: override defaults
RUNPOD_PUNCTUATE=true
RUNPOD_DENORMALIZE=true
RUNPOD_DENORMALIZE_STYLE=default
```

## API Format

### Input

```json
{
    "input": {
        "audio_base64": "<base64 encoded WAV audio>",
        "filename": "optional.wav",
        "punctuate": true,
        "denormalize": true,
        "denormalize_style": "default"
    }
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `audio_base64` | string | required | Base64 encoded WAV audio |
| `filename` | string | "audio.wav" | Original filename for logging |
| `punctuate` | bool | true | Add punctuation and capitalization |
| `denormalize` | bool | true | Convert numbers, dates, times |
| `denormalize_style` | string | "default" | Style: "default", "technical", "everyday" |

### Output (Success)

```json
{
    "text": "Včeraj sem spal 8 ur.",
    "raw_text": "včeraj sem spal osem ur",
    "processing_time": 12.5,
    "pipeline": ["asr", "punctuate", "denormalize"],
    "model_version": "protoverb-1.0"
}
```

| Field | Description |
|-------|-------------|
| `text` | Final processed text (after all pipeline steps) |
| `raw_text` | Original ASR output (no punctuation/denormalization) |
| `processing_time` | Total processing time in seconds |
| `pipeline` | List of steps applied (e.g., `["asr", "punctuate", "denormalize"]`) |
| `model_version` | Model version identifier |

### Output (Error)

```json
{
    "error": "Error description"
}
```

## Audio Requirements

- Format: WAV (16-bit PCM)
- Sample rate: 16kHz recommended
- Channels: Mono
- Max size: 50MB
- Max duration: ~5 minutes per request (longer audio is chunked client-side)

## Cost Estimate

- RunPod L4 GPU: ~$0.00026/sec
- Typical 5-minute audio: ~$0.02-0.03 (slightly higher with NLP pipeline)
- Cold start: 5-15s (models loading)

For 1-hour audio (chunked into ~15 chunks processed in parallel):
- Total GPU time: ~5-8 minutes
- Estimated cost: ~$0.10-0.15

## Denormalization Styles

| Style | Description | Example |
|-------|-------------|---------|
| `default` | Standard formatting | "8 ur", "25. december" |
| `technical` | Technical/scientific | "8 h", "25. 12." |
| `everyday` | Casual/conversational | "osem ur", "petindvajseti december" |

## Troubleshooting

### Cold Start Issues

The first request after idle period may take 5-15 seconds as all models load (ASR + Punctuator + Denormalizer). Subsequent requests will be fast.

### Memory Issues

With all models loaded, the container uses ~2-3GB GPU memory. L4 (24GB) or T4 (16GB) should work fine.

### Missing NLP Pipeline Steps

If `pipeline` only contains `["asr"]` but you expected punctuation/denormalization:
- Check container logs for model loading errors
- Ensure model files exist at correct paths in container
- Punctuator and denormalizer are optional - ASR will still work without them

### Model Loading Errors

Check that all files exist in the container:
- `/app/models/asr/conformer_ctc_bpe.nemo` (ASR)
- `/app/models/punctuator/nlp_tc_pc.nemo` (Punctuator)
- `/app/Slovene_denormalizator/denormalizer.py` (Denormalizer)

## Development

### Local Testing

```bash
# Build container (from runpod/ directory)
docker build -t slovene-asr-test .

# Run locally (requires GPU)
docker run --gpus all -p 8000:8000 slovene-asr-test

# Test with curl (with all pipeline steps)
curl -X POST http://localhost:8000/runsync \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "audio_base64": "...",
      "filename": "test.wav",
      "punctuate": true,
      "denormalize": true
    }
  }'

# Test ASR only (no NLP processing)
curl -X POST http://localhost:8000/runsync \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "audio_base64": "...",
      "punctuate": false,
      "denormalize": false
    }
  }'
```

### Testing Without GPU

The handler will fall back to CPU if no GPU is available, but performance will be significantly slower (~10x).

## Model Sources

| Model | Version | Source | License |
|-------|---------|--------|---------|
| PROTOVERB-ASR-E2E | 1.0 | [CLARIN-SI 11356/2024](https://clarin.si/repository/xmlui/handle/11356/2024) | Apache 2.0 |
| RSDO-DS2-P&C | 3.6 | [CLARIN-SI 11356/1735](https://www.clarin.si/repository/xmlui/handle/11356/1735) | Apache 2.0 |
| Slovene_denormalizator | - | [GitHub](https://github.com/clarinsi/Slovene_denormalizator) | Apache 2.0 |
