# GaMS LLM on RunPod Serverless

RunPod serverless handler for **GaMS (Generative Model for Slovene)** - a native Slovenian LLM for text cleanup and correction.

## Overview

| Spec | Value |
|------|-------|
| Model | [cjvt/GaMS-9B-Instruct](https://huggingface.co/cjvt/GaMS-9B-Instruct) |
| Parameters | 9B (based on Gemma 2) |
| VRAM Required | ~20GB |
| Recommended GPU | L4 24GB |
| Cold Start | ~10 seconds |
| Inference | ~3 seconds per transcript |

## Deployment

### 1. Build Docker Image

```bash
# Build for AMD64 (RunPod requirement)
docker buildx build --platform linux/amd64 \
  -t your-registry/gams-llm:v1.0 \
  --push .
```

### 2. Create RunPod Serverless Endpoint

1. Go to [RunPod Console → Serverless](https://www.runpod.io/console/serverless)
2. Click "New Endpoint"
3. Configure:
   - **Name**: `gams-llm-cleanup`
   - **Container Image**: `your-registry/gams-llm:v1.0`
   - **GPU**: L4 24GB (best value) or RTX 4090
   - **Idle Timeout**: 60 seconds (adjust based on traffic)
   - **Max Workers**: 1-3 (based on budget)
   - **FlashBoot**: Enable for faster cold starts

### 3. Configure Environment

Add to your `.env`:

```bash
# RunPod API Key (same as for ASR)
RUNPOD_API_KEY=rpa_xxxxx

# GaMS LLM Endpoint
RUNPOD_LLM_GAMS_ENDPOINT_ID=xxxxx
RUNPOD_LLM_GAMS_MODEL=GaMS-9B-Instruct

# Optional: Override defaults
RUNPOD_LLM_GAMS_TIMEOUT=120
RUNPOD_LLM_GAMS_MAX_RETRIES=3
RUNPOD_LLM_GAMS_DEFAULT_TEMPERATURE=0.3
RUNPOD_LLM_GAMS_DEFAULT_TOP_P=0.9
```

### 4. Use in Application

Set as default LLM provider:
```bash
DEFAULT_LLM_PROVIDER=runpod_llm_gams
```

Or specify per-request via API:
```json
{
  "llm_provider": "runpod_llm_gams"
}
```

## API Reference

### Input Schema

```json
{
  "input": {
    "prompt": "Formatted prompt with transcription text",
    "temperature": 0.3,
    "top_p": 0.9,
    "max_tokens": 2048
  }
}
```

### Batch Input (more cost-effective)

```json
{
  "input": {
    "batch": [
      {"prompt": "First prompt...", "id": "1"},
      {"prompt": "Second prompt...", "id": "2"}
    ],
    "temperature": 0.3,
    "top_p": 0.9,
    "max_tokens": 2048
  }
}
```

### Output Schema

**Single request:**
```json
{
  "text": "Cleaned text output",
  "processing_time": 3.2,
  "model_version": "gams-9b-instruct",
  "token_count": {
    "prompt": 150,
    "completion": 120
  }
}
```

**Batch request:**
```json
{
  "results": [
    {"id": "1", "text": "First cleaned text", "token_count": {...}},
    {"id": "2", "text": "Second cleaned text", "token_count": {...}}
  ],
  "processing_time": 5.5,
  "model_version": "gams-9b-instruct",
  "batch_size": 2,
  "total_token_count": {
    "prompt": 300,
    "completion": 240
  }
}
```

## Model Variants

| Model | Parameters | VRAM | Best For |
|-------|------------|------|----------|
| **GaMS-9B-Instruct** | 9B | ~20GB | Recommended, best value |
| GaMS-27B-Instruct | 27B | ~54GB | Higher quality (requires A100) |
| GaMS-2B-Instruct | 2B | ~8GB | Lightweight, fastest |
| GaMS-1B-Chat | 1B | ~4GB | Testing, minimal resources |

To use a different model, set `GAMS_MODEL_ID` environment variable in the Dockerfile or RunPod endpoint configuration.

## Prompt Format

GaMS-Instruct models use ChatML format:

```
<|im_start|>user
Popravi naslednji prepis govora...
<|im_end|>
<|im_start|>assistant
```

The handler automatically wraps your prompt in this format.

## Resources

- [GaMS-9B-Instruct on HuggingFace](https://huggingface.co/cjvt/GaMS-9B-Instruct)
- [CJVT (Centre for Language Resources)](https://www.cjvt.si/)
- [RunPod Serverless Docs](https://docs.runpod.io/serverless/overview)
- [RunPod Pricing](https://docs.runpod.io/serverless/pricing)
- [vLLM Documentation](https://docs.vllm.ai/)
