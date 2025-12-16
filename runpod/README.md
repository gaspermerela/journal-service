# RunPod Slovenian Transcription Handler

This directory contains the serverless handler for running RSDO Slovenian ASR on RunPod GPU.

## Overview

The handler uses the [RSDO-DS2-ASR-E2E 2.0](https://www.clarin.si/repository/xmlui/handle/11356/1737) model which is purpose-built for Slovenian speech recognition with 5.58% WER (compared to ~10-15% for Whisper on Slovenian).

## Files

- `handler.py` - RunPod serverless handler
- `Dockerfile` - Container image for RunPod
- `requirements.txt` - Python dependencies

## Setup

### 1. Download the RSDO Model

```bash
# From project root
./scripts/download_rsdo_model.sh
```

This downloads the ~430MB model to `models/conformer_ctc_bpe.nemo`.

### 2. Build Docker Image

```bash
# From project root
docker build -t your-dockerhub-username/rsdo-slovenian-asr:latest -f runpod/Dockerfile .
```

### 3. Push to Docker Hub

```bash
docker push your-dockerhub-username/rsdo-slovenian-asr:latest
```

### 4. Create RunPod Serverless Endpoint

1. Go to [RunPod Serverless](https://www.runpod.io/console/serverless)
2. Click "New Endpoint"
3. Configure:
   - **Container Image**: `your-dockerhub-username/rsdo-slovenian-asr:latest`
   - **GPU Type**: L4 or T4 (cheapest options that work)
   - **Max Workers**: 3 (or as needed)
   - **Idle Timeout**: 60 seconds
   - **Execution Timeout**: 300 seconds (5 minutes)
   - **Region**: EU-RO-1 (Romania) for GDPR compliance
4. Copy the Endpoint ID

### 5. Configure Environment Variables

Add to your `.env`:

```bash
TRANSCRIPTION_PROVIDER=runpod
RUNPOD_API_KEY=your_runpod_api_key
RUNPOD_ENDPOINT_ID=your_endpoint_id
```

## API Format

### Input

```json
{
    "input": {
        "audio_base64": "<base64 encoded WAV audio>",
        "filename": "optional.wav"
    }
}
```

### Output (Success)

```json
{
    "text": "Transkriptirano slovensko besedilo",
    "processing_time": 12.5
}
```

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
- Typical 5-minute audio: ~$0.01-0.02
- Cold start: 500ms-1s (negligible cost)

For 1-hour audio (chunked into ~15 chunks processed in parallel):
- Total GPU time: ~3-5 minutes
- Estimated cost: ~$0.05-0.10

## Troubleshooting

### Cold Start Issues

The first request after idle period may take 5-30 seconds as the model loads. Subsequent requests will be fast.

### Memory Issues

If you see OOM errors, ensure your RunPod configuration has at least 16GB GPU memory. L4 (24GB) or T4 (16GB) should work.

### Model Loading Errors

Ensure the model file exists at `/app/models/conformer_ctc_bpe.nemo` in the container. Check that the Docker build copied it correctly.

## Development

### Local Testing

```bash
# Build container
docker build -t rsdo-asr-test -f runpod/Dockerfile .

# Run locally (requires GPU)
docker run --gpus all -p 8000:8000 rsdo-asr-test

# Test with curl
curl -X POST http://localhost:8000/runsync \
  -H "Content-Type: application/json" \
  -d '{"input": {"audio_base64": "...", "filename": "test.wav"}}'
```

### Testing Without GPU

The handler will fall back to CPU if no GPU is available, but performance will be significantly slower.
