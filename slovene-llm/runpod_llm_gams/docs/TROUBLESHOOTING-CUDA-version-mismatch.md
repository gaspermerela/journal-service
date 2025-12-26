# GaMS LLM Troubleshooting Guide

## CUDA PTX Version Mismatch (32GB+ GPU)

**Date:** 2025-12-26
**Status:** Unresolved
**Severity:** Critical - prevents model initialization

---

### Symptom

After upgrading to a GPU with sufficient VRAM (32GB+), the model loads successfully and KV cache allocation works, but fails during CUDA graph capture with:

```
torch.AcceleratorError: CUDA error: the provided PTX was compiled with an unsupported toolchain.
CUDA kernel errors might be asynchronously reported at some other API call, so the stacktrace below might be incorrect.
For debugging consider passing CUDA_LAUNCH_BLOCKING=1
Compile with `TORCH_USE_CUDA_DSA` to enable device-side assertions.

Search for the following error message `cudaErrorUnsupportedPtxVersion'
```

The failure occurs specifically during the `Capturing CUDA graphs (decode, FULL)` phase.

---

### Environment

| Component | Value |
|-----------|-------|
| GPU | NVIDIA GPU with 32GB VRAM |
| Docker CUDA | 11.8.0 |
| vLLM | 0.13.0 |
| Model | cjvt/GaMS-9B-Instruct |
| Architecture | Gemma2ForCausalLM |
| dtype | bfloat16 |

---

### Root Cause Analysis

The error indicates a **CUDA version mismatch** between:
1. The Docker base image (CUDA 11.8)
2. The compiled vLLM/Flash Attention binaries (likely compiled for CUDA 12.x)

PTX (Parallel Thread Execution) is NVIDIA's intermediate assembly language. When PyTorch/vLLM tries to execute CUDA kernels compiled for a newer CUDA toolkit on an older runtime, this error occurs.

**Key observation:** The PIECEWISE CUDA graph capture succeeds, but FULL decode capture fails - suggesting some kernels are compatible while others require newer CUDA.

---

### What's Working

From the logs, these stages complete successfully:
- Model loading (17.22 GiB, 25 seconds)
- KV cache allocation (8.55 GiB available - plenty of headroom)
- Flash Attention backend initialization
- PIECEWISE CUDA graph capture (51/51 complete)

The failure is specifically in the FULL decode CUDA graph capture phase.

---

### Solutions

#### Option A: Upgrade Docker Base Image to CUDA 12.x (Recommended)

Update the Dockerfile to use a CUDA 12.x base image:

```dockerfile
# OLD: CUDA 11.8
FROM runpod/pytorch:2.4.0-py3.11-cuda11.8.0-devel-ubuntu22.04

# NEW: CUDA 12.1+ (vLLM 0.13 requires CUDA 12.1+)
FROM runpod/pytorch:2.4.0-py3.11-cuda12.1.0-devel-ubuntu22.04
```

**Pros:**
- Proper fix that enables all optimizations
- vLLM 0.13+ officially requires CUDA 12.1+

**Cons:**
- Requires rebuilding Docker image
- Need to verify RunPod GPU compatibility

---

#### Option B: Use `enforce_eager=True` (Quick Workaround)

Disable CUDA graphs entirely to bypass the incompatible kernels:

```python
llm = LLM(
    model=MODEL_PATH,
    dtype="bfloat16",
    max_model_len=4096,
    trust_remote_code=True,
    enforce_eager=True,  # Disable CUDA graphs
)
```

**Pros:**
- Quick fix, no Docker rebuild needed
- Model will run

**Cons:**
- Slower inference (no CUDA graph optimization)
- May still have issues with Flash Attention kernels

---

#### Option C: Downgrade vLLM to CUDA 11.8 Compatible Version

Use an older vLLM version that was compiled for CUDA 11.8:

```dockerfile
# Install vLLM version compatible with CUDA 11.8
RUN pip install vllm==0.5.5  # Last version with good CUDA 11.8 support
```

**Pros:**
- Works with existing Docker base image

**Cons:**
- Older vLLM version, may lack features/optimizations
- May have other compatibility issues with newer models

---

### Recommended Path Forward

1. **Immediate:** Try `enforce_eager=True` to confirm model works otherwise
2. **Short term:** Rebuild Docker image with CUDA 12.1+ base image
3. **Verify:** Check vLLM 0.13 release notes for CUDA requirements

---

### Relevant Log Excerpts (32GB GPU)

<details>
<summary>Successful initialization up to CUDA graph capture (click to expand)</summary>

```
INFO Available KV cache memory: 8.55 GiB
INFO GPU KV cache size: 26,656 tokens
INFO Maximum concurrency for 4,096 tokens per request: 6.50x
INFO Capturing CUDA graphs (mixed prefill-decode, PIECEWISE): 100%|██████████| 51/51
INFO Capturing CUDA graphs (decode, FULL):   0%|          | 0/35 [00:00<?, ?it/s]
ERROR EngineCore failed to start.
ERROR torch.AcceleratorError: CUDA error: the provided PTX was compiled with an unsupported toolchain.
```

</details>

---

### References

- [vLLM CUDA Requirements](https://docs.vllm.ai/en/latest/getting_started/installation.html)
- [GaMS Model Card](https://huggingface.co/cjvt/GaMS-9B-Instruct)
- [Gemma 2 Architecture](https://ai.google.dev/gemma)
- [RunPod GPU Specifications](https://docs.runpod.io/pods/gpus)