"""
RunPod serverless handler for RSDO Slovenian ASR.

This handler runs on RunPod serverless GPU and processes audio transcription
requests using the RSDO NeMo model.

Input:
    {
        "input": {
            "audio_base64": "<base64 encoded WAV audio>",
            "filename": "optional_filename.wav"
        }
    }

Output:
    {
        "text": "Transkriptirano slovensko besedilo",
        "processing_time": 12.5
    }
"""
import base64
import logging
import os
import tempfile
import time
from pathlib import Path

import runpod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("rsdo_handler")

# Global model instance - loaded once at container startup
MODEL = None

# Model path - baked into Docker image or mounted volume
MODEL_PATH = os.environ.get("MODEL_PATH", "/app/models/conformer_ctc_bpe.nemo")

# Maximum audio size (50MB)
MAX_AUDIO_SIZE = 50 * 1024 * 1024


def load_model():
    """
    Load RSDO NeMo model at container startup.

    The model is loaded once and kept in memory for subsequent requests.
    This minimizes cold start impact for repeated requests.
    """
    global MODEL

    if MODEL is not None:
        logger.info("Model already loaded, skipping")
        return

    logger.info(f"Loading RSDO model from {MODEL_PATH}")
    start_time = time.time()

    try:
        import nemo.collections.asr as nemo_asr

        MODEL = nemo_asr.models.EncDecCTCModelBPE.restore_from(MODEL_PATH)

        # Move to GPU if available
        cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
        if cuda_visible != "" and cuda_visible.lower() != "none":
            MODEL = MODEL.cuda()
            logger.info("Model moved to GPU")
        else:
            logger.info("Running on CPU (no GPU available)")

        MODEL.eval()

        load_time = time.time() - start_time
        logger.info(f"Model loaded successfully in {load_time:.2f}s")

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


def handler(job):
    """
    RunPod serverless handler for audio transcription.

    Args:
        job: RunPod job dict with "input" containing:
            - audio_base64: Base64 encoded WAV audio
            - filename: Optional original filename

    Returns:
        dict with:
            - text: Transcribed Slovenian text
            - processing_time: Time taken in seconds
        OR
            - error: Error message if transcription failed
    """
    global MODEL

    # Load model if not already loaded (cold start)
    if MODEL is None:
        try:
            load_model()
        except Exception as e:
            return {"error": f"Failed to load model: {str(e)}"}

    # Extract input
    job_input = job.get("input", {})
    audio_base64 = job_input.get("audio_base64")
    filename = job_input.get("filename", "audio.wav")

    # Validate input
    if not audio_base64:
        return {"error": "No audio_base64 provided in input"}

    # Decode audio
    try:
        audio_bytes = base64.b64decode(audio_base64)
    except Exception as e:
        return {"error": f"Failed to decode base64 audio: {str(e)}"}

    # Validate size
    if len(audio_bytes) > MAX_AUDIO_SIZE:
        return {"error": f"Audio file too large: {len(audio_bytes)} bytes (max: {MAX_AUDIO_SIZE})"}

    if len(audio_bytes) < 100:
        return {"error": "Audio file too small - likely invalid"}

    # Process transcription
    tmp_path = None
    try:
        start_time = time.time()

        # Save to temp file (NeMo requires file path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        logger.info(f"Transcribing {filename} ({len(audio_bytes)} bytes)")

        # Transcribe using NeMo model
        transcriptions = MODEL.transcribe([tmp_path])

        # Extract text
        text = transcriptions[0] if transcriptions else ""
        text = text.strip()

        processing_time = time.time() - start_time

        logger.info(
            f"Transcription complete: {len(text)} chars in {processing_time:.2f}s"
        )

        return {
            "text": text,
            "processing_time": processing_time
        }

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return {"error": f"Transcription failed: {str(e)}"}

    finally:
        # Cleanup temp file
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def health_check():
    """
    Health check for the handler.

    Returns True if model is loaded and ready.
    """
    return MODEL is not None


# RunPod entry point
if __name__ == "__main__":
    logger.info("Starting RSDO ASR serverless handler")

    # Pre-load model during container initialization
    # This reduces cold start latency for first request
    try:
        load_model()
        logger.info("Model pre-loaded during startup")
    except Exception as e:
        logger.warning(f"Failed to pre-load model (will load on first request): {e}")

    # Start RunPod serverless worker
    runpod.serverless.start({"handler": handler})
