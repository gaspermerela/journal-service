"""
RunPod Serverless Handler for GaMS (Generative Model for Slovene) LLM.

This handler uses vLLM for optimized inference of the GaMS-9B-Instruct model.
Supports both single and batch text cleanup requests.

Model: cjvt/GaMS-9B-Instruct (based on Gemma 2, trained on Slovenian)
GPU: L4 24GB recommended ($0.684/hr on RunPod Flex)
"""
import os
import time
from typing import Any, Dict, List, Optional

import runpod
from vllm import LLM, SamplingParams

# Configuration from environment
MODEL_ID = os.getenv("GAMS_MODEL_ID", "cjvt/GaMS-9B-Instruct")
MODEL_PATH = os.getenv("GAMS_MODEL_PATH", None)  # Use local path if provided
GPU_MEMORY_UTILIZATION = float(os.getenv("GPU_MEMORY_UTILIZATION", "0.90"))
MAX_MODEL_LEN = int(os.getenv("MAX_MODEL_LEN", "4096"))

# Default sampling parameters
DEFAULT_TEMPERATURE = 0.3
DEFAULT_TOP_P = 0.9
DEFAULT_MAX_TOKENS = 2048

# Global model instance (loaded once at container startup)
llm: Optional[LLM] = None


def load_model() -> LLM:
    """
    Load GaMS model using vLLM.

    Model is loaded once at container startup and reused across requests.
    This minimizes cold start impact for subsequent requests.
    """
    global llm

    if llm is not None:
        return llm

    print(f"Loading GaMS model: {MODEL_PATH or MODEL_ID}")
    start_time = time.time()

    # Use local path if available (faster startup), otherwise download from HF
    model_source = MODEL_PATH if MODEL_PATH and os.path.exists(MODEL_PATH) else MODEL_ID

    llm = LLM(
        model=model_source,
        dtype="float16",  # FP16 for L4 GPU
        gpu_memory_utilization=GPU_MEMORY_UTILIZATION,
        max_model_len=MAX_MODEL_LEN,
        trust_remote_code=True,  # Required for some GaMS variants
    )

    elapsed = time.time() - start_time
    print(f"Model loaded in {elapsed:.2f}s")

    return llm


def format_chatml_prompt(prompt: str) -> str:
    """
    Format prompt in ChatML format for GaMS-Instruct models.

    GaMS-Instruct models expect ChatML format:
    <|im_start|>user
    {prompt}<|im_end|>
    <|im_start|>assistant

    Args:
        prompt: Raw prompt text (already formatted with transcription)

    Returns:
        ChatML-formatted prompt string
    """
    return f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"


def create_sampling_params(
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> SamplingParams:
    """
    Create vLLM SamplingParams with provided or default values.

    Args:
        temperature: Sampling temperature (0.0-2.0). Lower = more deterministic.
        top_p: Nucleus sampling parameter (0.0-1.0).
        max_tokens: Maximum tokens to generate.

    Returns:
        Configured SamplingParams instance
    """
    return SamplingParams(
        temperature=temperature if temperature is not None else DEFAULT_TEMPERATURE,
        top_p=top_p if top_p is not None else DEFAULT_TOP_P,
        max_tokens=max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS,
        stop=["<|im_end|>", "</s>"],  # Stop tokens for ChatML
    )


def process_single(
    prompt: str,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Process a single cleanup request.

    Args:
        prompt: Formatted prompt (will be wrapped in ChatML)
        temperature: Optional sampling temperature
        top_p: Optional nucleus sampling parameter
        max_tokens: Optional max tokens to generate

    Returns:
        Dict with text, processing_time, and model info
    """
    model = load_model()

    start_time = time.time()

    # Format prompt for ChatML
    formatted_prompt = format_chatml_prompt(prompt)

    # Create sampling parameters
    sampling_params = create_sampling_params(temperature, top_p, max_tokens)

    # Generate
    outputs = model.generate([formatted_prompt], sampling_params)

    # Extract generated text
    generated_text = outputs[0].outputs[0].text.strip()

    processing_time = time.time() - start_time

    return {
        "text": generated_text,
        "processing_time": round(processing_time, 3),
        "model_version": MODEL_ID.split("/")[-1].lower(),
        "token_count": {
            "prompt": len(outputs[0].prompt_token_ids),
            "completion": len(outputs[0].outputs[0].token_ids),
        },
    }


def process_batch(
    batch: List[Dict[str, Any]],
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Process a batch of cleanup requests efficiently.

    Batch processing is more cost-effective as it amortizes cold start
    across multiple requests and enables vLLM's batching optimizations.

    Args:
        batch: List of dicts with 'prompt' and optional 'id' keys
        temperature: Optional sampling temperature (applied to all)
        top_p: Optional nucleus sampling parameter (applied to all)
        max_tokens: Optional max tokens (applied to all)

    Returns:
        Dict with results list, total processing_time, and model info
    """
    model = load_model()

    start_time = time.time()

    # Extract prompts and IDs
    prompts = []
    ids = []
    for i, item in enumerate(batch):
        prompt = item.get("prompt")
        if not prompt:
            raise ValueError(f"Batch item {i} missing 'prompt' field")
        prompts.append(format_chatml_prompt(prompt))
        ids.append(item.get("id", str(i)))

    # Create sampling parameters
    sampling_params = create_sampling_params(temperature, top_p, max_tokens)

    # Generate all at once (vLLM handles batching efficiently)
    outputs = model.generate(prompts, sampling_params)

    # Build results
    results = []
    total_prompt_tokens = 0
    total_completion_tokens = 0

    for i, output in enumerate(outputs):
        generated_text = output.outputs[0].text.strip()
        prompt_tokens = len(output.prompt_token_ids)
        completion_tokens = len(output.outputs[0].token_ids)

        total_prompt_tokens += prompt_tokens
        total_completion_tokens += completion_tokens

        results.append({
            "id": ids[i],
            "text": generated_text,
            "token_count": {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
            },
        })

    processing_time = time.time() - start_time

    return {
        "results": results,
        "processing_time": round(processing_time, 3),
        "model_version": MODEL_ID.split("/")[-1].lower(),
        "batch_size": len(batch),
        "total_token_count": {
            "prompt": total_prompt_tokens,
            "completion": total_completion_tokens,
        },
    }


def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod serverless handler entry point.

    Supports two modes:
    1. Single request: {"input": {"prompt": "...", "temperature": 0.3, ...}}
    2. Batch request: {"input": {"batch": [{"prompt": "...", "id": "1"}, ...], ...}}

    Input fields:
        - prompt: str - Formatted prompt for single request
        - batch: list - List of {"prompt": str, "id": str} for batch request
        - temperature: float - Sampling temperature (0.0-2.0), default 0.3
        - top_p: float - Nucleus sampling (0.0-1.0), default 0.9
        - max_tokens: int - Max tokens to generate, default 2048

    Returns:
        Single mode: {"text": str, "processing_time": float, ...}
        Batch mode: {"results": [...], "processing_time": float, ...}
        Error: {"error": str}
    """
    try:
        job_input = job.get("input", {})

        # Extract common parameters
        temperature = job_input.get("temperature")
        top_p = job_input.get("top_p")
        max_tokens = job_input.get("max_tokens")

        # Check for batch vs single mode
        batch = job_input.get("batch")
        prompt = job_input.get("prompt")

        if batch:
            # Batch processing
            if not isinstance(batch, list) or len(batch) == 0:
                return {"error": "batch must be a non-empty list"}

            return process_batch(
                batch=batch,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )

        elif prompt:
            # Single processing
            if not isinstance(prompt, str) or not prompt.strip():
                return {"error": "prompt must be a non-empty string"}

            return process_single(
                prompt=prompt,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )

        else:
            return {"error": "Provide either 'prompt' (single) or 'batch' (multiple) in input"}

    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"Handler error: {error_msg}")
        print(traceback.format_exc())
        return {"error": error_msg}


# Pre-load model at container startup for faster first request
print("Initializing GaMS LLM handler...")
try:
    load_model()
    print("Model pre-loaded successfully")
except Exception as e:
    print(f"Warning: Model pre-load failed: {e}")
    print("Model will be loaded on first request")

# Start RunPod serverless handler
runpod.serverless.start({"handler": handler})
