"""
RunPod serverless handler for Slovenian ASR with NLP pipeline.

This handler runs on RunPod serverless GPU and processes audio transcription
requests using the PROTOVERB NeMo model with optional punctuation and denormalization.

Pipeline:
    Audio -> ASR (PROTOVERB) -> Punctuation (optional) -> Denormalization (optional)

Input:
    {
        "input": {
            "audio_base64": "<base64 encoded WAV audio>",
            "filename": "optional_filename.wav",
            "punctuate": true,           # Add punctuation & capitalization (default: true)
            "denormalize": true,         # Convert numbers, dates, times (default: true)
            "denormalize_style": "default"  # Options: default, technical, everyday
        }
    }

Output:
    {
        "text": "Včeraj sem spal 8 ur.",     # Final processed text
        "raw_text": "včeraj sem spal osem ur",  # Original ASR output
        "processing_time": 12.5,
        "pipeline": ["asr", "punctuate", "denormalize"],
        "model_version": "protoverb-1.0"
    }
"""
import base64
import logging
import os
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Dict, Any, List

import runpod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("slovene_asr_handler")

# Global model instances - loaded once at container startup
ASR_MODEL = None
PUNCTUATOR_MODEL = None
DENORMALIZER = None

# Model paths - baked into Docker image
ASR_MODEL_PATH = os.environ.get("ASR_MODEL_PATH", "/app/models/asr/conformer_ctc_bpe.nemo")
PUNCTUATOR_MODEL_PATH = os.environ.get("PUNCTUATOR_MODEL_PATH", "/app/models/punctuator/nlp_tc_pc.nemo")

# Denormalizer path (Python package)
DENORMALIZER_PATH = os.environ.get("DENORMALIZER_PATH", "/app/Slovene_denormalizator")

# Maximum audio size (50MB)
MAX_AUDIO_SIZE = 50 * 1024 * 1024

# Model version identifier
MODEL_VERSION = "protoverb-1.0"


def load_asr_model():
    """
    Load PROTOVERB ASR model at container startup.
    """
    global ASR_MODEL

    if ASR_MODEL is not None:
        logger.info("ASR model already loaded, skipping")
        return

    logger.info(f"Loading PROTOVERB ASR model from {ASR_MODEL_PATH}")
    start_time = time.time()

    try:
        import nemo.collections.asr as nemo_asr

        ASR_MODEL = nemo_asr.models.EncDecCTCModelBPE.restore_from(ASR_MODEL_PATH)

        # Move to GPU if available
        cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
        if cuda_visible != "" and cuda_visible.lower() != "none":
            ASR_MODEL = ASR_MODEL.cuda()
            logger.info("ASR model moved to GPU")
        else:
            logger.info("ASR model running on CPU")

        ASR_MODEL.eval()

        load_time = time.time() - start_time
        logger.info(f"ASR model loaded successfully in {load_time:.2f}s")

    except Exception as e:
        logger.error(f"Failed to load ASR model: {e}")
        raise


def load_punctuator_model():
    """
    Load Slovenian punctuation & capitalization model.
    """
    global PUNCTUATOR_MODEL

    if PUNCTUATOR_MODEL is not None:
        logger.info("Punctuator model already loaded, skipping")
        return

    if not os.path.exists(PUNCTUATOR_MODEL_PATH):
        logger.warning(f"Punctuator model not found at {PUNCTUATOR_MODEL_PATH}, punctuation disabled")
        return

    logger.info(f"Loading punctuator model from {PUNCTUATOR_MODEL_PATH}")
    start_time = time.time()

    try:
        from nemo.collections.nlp.models import PunctuationCapitalizationModel

        PUNCTUATOR_MODEL = PunctuationCapitalizationModel.restore_from(PUNCTUATOR_MODEL_PATH)

        # Move to GPU if available
        cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
        if cuda_visible != "" and cuda_visible.lower() != "none":
            PUNCTUATOR_MODEL = PUNCTUATOR_MODEL.cuda()
            logger.info("Punctuator model moved to GPU")
        else:
            logger.info("Punctuator model running on CPU")

        PUNCTUATOR_MODEL.eval()

        load_time = time.time() - start_time
        logger.info(f"Punctuator model loaded successfully in {load_time:.2f}s")

    except Exception as e:
        logger.error(f"Failed to load punctuator model: {e}")
        # Don't raise - punctuation is optional


def load_denormalizer():
    """
    Load Slovenian text denormalizer.
    """
    global DENORMALIZER

    if DENORMALIZER is not None:
        logger.info("Denormalizer already loaded, skipping")
        return

    if not os.path.exists(DENORMALIZER_PATH):
        logger.warning(f"Denormalizer not found at {DENORMALIZER_PATH}, denormalization disabled")
        return

    logger.info(f"Loading denormalizer from {DENORMALIZER_PATH}")

    try:
        # Add denormalizer to path
        if DENORMALIZER_PATH not in sys.path:
            sys.path.insert(0, DENORMALIZER_PATH)

        # The denormalizer uses hardcoded relative paths (data/...)
        # We need to change to its directory before importing
        original_cwd = os.getcwd()
        os.chdir(DENORMALIZER_PATH)

        try:
            from denormalizer import denormalize as denorm_func
            DENORMALIZER = denorm_func
            logger.info("Denormalizer loaded successfully")
        finally:
            os.chdir(original_cwd)

    except Exception as e:
        logger.error(f"Failed to load denormalizer: {e}")
        # Don't raise - denormalization is optional


def load_models_parallel(need_asr: bool = True, need_punct: bool = True, need_denorm: bool = True):
    """
    Load required models in parallel.

    Only loads models that are needed AND not already loaded.
    If multiple models need loading, they load in parallel.
    """
    global ASR_MODEL, PUNCTUATOR_MODEL, DENORMALIZER

    loaders = []
    if need_asr and ASR_MODEL is None:
        loaders.append(("ASR", load_asr_model))
    if need_punct and PUNCTUATOR_MODEL is None:
        loaders.append(("Punctuator", load_punctuator_model))
    if need_denorm and DENORMALIZER is None:
        loaders.append(("Denormalizer", load_denormalizer))

    if not loaders:
        return  # All already loaded

    names = [name for name, _ in loaders]
    logger.info(f"Loading models: {', '.join(names)}")
    start_time = time.time()

    if len(loaders) == 1:
        # Single model - load directly
        loaders[0][1]()
    else:
        # Multiple models - load in parallel
        with ThreadPoolExecutor(max_workers=len(loaders)) as executor:
            futures = [executor.submit(fn) for _, fn in loaders]
            wait(futures)

    load_time = time.time() - start_time
    logger.info(f"Models loaded in {load_time:.2f}s")


def apply_punctuation(text: str) -> str:
    """
    Apply punctuation and capitalization to text.

    Args:
        text: Raw lowercase text without punctuation

    Returns:
        Text with punctuation and proper capitalization
    """
    global PUNCTUATOR_MODEL

    if PUNCTUATOR_MODEL is None:
        logger.warning("Punctuator not available, returning original text")
        return text

    if not text or not text.strip():
        return text

    try:
        # NeMo punctuator expects list of strings
        results = PUNCTUATOR_MODEL.add_punctuation_capitalization([text])
        return results[0] if results else text

    except Exception as e:
        logger.error(f"Punctuation failed: {e}")
        return text


def apply_denormalization(text: str, style: str = "default") -> str:
    """
    Apply text denormalization (numbers, dates, times, etc.).

    Args:
        text: Text to denormalize
        style: Denormalization style - "default", "technical", or "everyday"

    Returns:
        Denormalized text with proper number/date formatting
    """
    global DENORMALIZER

    if DENORMALIZER is None:
        logger.warning("Denormalizer not available, returning original text")
        return text

    if not text or not text.strip():
        return text

    try:
        # Call denormalizer with style config
        result = DENORMALIZER(text, custom_config=style)

        # Extract denormalized string from result
        if isinstance(result, dict):
            return result.get("denormalized_string", text)
        return str(result)

    except Exception as e:
        logger.error(f"Denormalization failed: {e}")
        return text


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio file using PROTOVERB ASR model.

    Args:
        audio_path: Path to audio file

    Returns:
        Transcribed text (lowercase, no punctuation)
    """
    global ASR_MODEL

    if ASR_MODEL is None:
        raise RuntimeError("ASR model not loaded")

    transcriptions = ASR_MODEL.transcribe([audio_path])
    return transcriptions[0].strip() if transcriptions else ""


def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod serverless handler for audio transcription with NLP pipeline.

    Args:
        job: RunPod job dict with "input" containing:
            - audio_base64: Base64 encoded WAV audio
            - filename: Optional original filename
            - punctuate: Whether to add punctuation (default: True)
            - denormalize: Whether to denormalize text (default: True)
            - denormalize_style: Denormalization style (default: "default")

    Returns:
        dict with:
            - text: Final processed text
            - raw_text: Original ASR output
            - processing_time: Time taken in seconds
            - pipeline: List of processing steps applied
            - model_version: Model version identifier
        OR
            - error: Error message if processing failed
    """
    # Extract input
    job_input = job.get("input", {})
    audio_base64 = job_input.get("audio_base64")
    filename = job_input.get("filename", "audio.wav")

    # Processing options (defaults: both enabled)
    do_punctuate = job_input.get("punctuate", True)
    do_denormalize = job_input.get("denormalize", True)
    denormalize_style = job_input.get("denormalize_style", "default")

    # Load required models (parallel if multiple needed)
    try:
        load_models_parallel(
            need_asr=True,
            need_punct=do_punctuate,
            need_denorm=do_denormalize
        )
    except Exception as e:
        return {"error": f"Failed to load models: {str(e)}"}

    # Validate denormalize_style
    valid_styles = ["default", "technical", "everyday"]
    if denormalize_style not in valid_styles:
        logger.warning(f"Invalid denormalize_style '{denormalize_style}', using 'default'")
        denormalize_style = "default"

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
        pipeline_steps: List[str] = []

        # Save to temp file (NeMo requires file path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        logger.info(f"Processing {filename} ({len(audio_bytes)} bytes)")
        logger.info(f"Options: punctuate={do_punctuate}, denormalize={do_denormalize}, style={denormalize_style}")

        # Step 1: ASR transcription
        raw_text = transcribe_audio(tmp_path)
        pipeline_steps.append("asr")
        logger.info(f"ASR complete: {len(raw_text)} chars")

        # Start with raw text
        text = raw_text

        # Step 2: Punctuation (optional)
        if do_punctuate and PUNCTUATOR_MODEL is not None:
            text = apply_punctuation(text)
            pipeline_steps.append("punctuate")
            logger.info(f"Punctuation complete: {len(text)} chars")

        # Step 3: Denormalization (optional)
        if do_denormalize and DENORMALIZER is not None:
            text = apply_denormalization(text, style=denormalize_style)
            pipeline_steps.append("denormalize")
            logger.info(f"Denormalization complete: {len(text)} chars")

        processing_time = time.time() - start_time

        logger.info(
            f"Processing complete: pipeline={pipeline_steps}, "
            f"time={processing_time:.2f}s, output={len(text)} chars"
        )

        return {
            "text": text,
            "raw_text": raw_text,
            "processing_time": processing_time,
            "pipeline": pipeline_steps,
            "model_version": MODEL_VERSION
        }

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return {"error": f"Processing failed: {str(e)}"}

    finally:
        # Cleanup temp file
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def health_check() -> bool:
    """
    Health check for the handler.

    Returns True if ASR model is loaded and ready.
    Punctuator and denormalizer are optional.
    """
    return ASR_MODEL is not None


# RunPod entry point
if __name__ == "__main__":
    logger.info("Starting Slovenian ASR serverless handler")
    logger.info(f"Model version: {MODEL_VERSION}")

    # Pre-load all models in parallel (optimizes for common full-pipeline case)
    load_models_parallel(need_asr=True, need_punct=True, need_denorm=True)

    # Start RunPod serverless worker
    runpod.serverless.start({"handler": handler})
