"""
RunPod serverless handler for Slovenian ASR with NLP pipeline and speaker diarization.

This handler runs on RunPod serverless GPU and processes audio transcription
requests using the PROTOVERB NeMo model with optional punctuation, denormalization,
and speaker diarization.

Pipeline:
    Without diarization:
        Audio -> ASR (PROTOVERB) -> Punctuation (optional) -> Denormalization (optional)

    With diarization (DIARIZE-FIRST architecture):
        Audio -> Diarization -> Pre-merge -> [ASR + NFA per segment] -> Merge -> Punct -> Denorm

        Phase 1: Diarization (full audio)
            - Detect speaker segments with timestamps
            - Uses TitaNet-Large embeddings + clustering

        Phase 1.5: Pre-merge short segments (for ASR quality)
            - Merge adjacent same-speaker segments < 3s
            - Gives PROTOVERB more acoustic context

        Phase 2: Process segments in parallel
            - Extract audio with 0.5s context padding before/after
            - Run ASR on segment (captures words dropped on full audio)
            - Run NFA for word-level timestamps (skipped on segments < 2s)

        Phase 3: Merge consecutive same-speaker segments

        Phase 4: Apply punctuation and denormalization per segment

    Quality optimizations:
        - MIN_SEGMENT_FOR_ASR (3.0s): Pre-merge short segments for context
        - MAX_SEGMENT_FOR_ASR (30.0s): Cap merged segments to prevent NFA slowdown
        - CONTEXT_PADDING (0.5s): Add audio context around segment boundaries
        - MIN_SEGMENT_FOR_NFA (2.0s): Skip NFA on tiny segments (overhead not worth it)

    Why DIARIZE-FIRST?
        The old architecture (ASR first, then diarize) had a critical flaw:
        ASR on long audio (3-5 min) would drop words during speaker transitions.
        By diarizing first and running ASR on short segments (5-30s), we capture
        all utterances that would otherwise be lost.

Input:
    {
        "input": {
            "audio_base64": "<base64 encoded WAV audio>",
            "filename": "optional_filename.wav",
            "punctuate": true,              # Add punctuation & capitalization (default: true)
            "denormalize": true,            # Convert numbers, dates, times (default: true)
            "denormalize_style": "default", # Options: default, technical, everyday
            "enable_diarization": false,    # Identify speakers (default: false)
            "speaker_count": null,          # Known speaker count, null=auto (default: null)
            "max_speakers": 10              # Max speakers for auto-detect (default: 10)
        }
    }

Output (without diarization):
    {
        "text": "Včeraj sem spal 8 ur.",
        "raw_text": "včeraj sem spal osem ur",
        "processing_time": 12.5,
        "pipeline": ["asr", "punctuate", "denormalize"],
        "model_version": "protoverb-1.0",
        "diarization_applied": false
    }

Output (with diarization):
    {
        "text": "Speaker 1: Pozdravljeni. Speaker 2: Hvala.",
        "raw_text": "pozdravljeni hvala",
        "processing_time": 15.2,
        "pipeline": ["asr", "align", "diarize", "punctuate", "denormalize"],
        "model_version": "protoverb-1.0",
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
"""
import base64
import logging
import os
import sys
import tempfile
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Dict, Any, List

import runpod

# Configure logging for our handler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("slovene_asr_handler")

# Suppress HuggingFace/transformers warnings
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
warnings.filterwarnings("ignore", message=".*resume_download.*")
warnings.filterwarnings("ignore", message=".*Some weights.*were not initialized.*")

# Global model instances - loaded once at container startup
ASR_MODEL = None
PUNCTUATOR_MODEL = None
DENORMALIZER = None

# Diarization models
# Speaker diarization answers "WHO spoke WHEN" and requires two models:
#
# 1. VAD (Voice Activity Detection) - MarbleNet
#    Detects WHEN someone is speaking vs silence/noise.
#    Output: time ranges like [(0.0s-2.5s, speech), (2.5s-3.0s, silence), ...]
#    Without VAD, we'd waste compute analyzing silence.
#
# 2. Speaker Embeddings - TitaNet-Large
#    Creates a "voiceprint" (vector) for each speech segment.
#    Similar voices → similar vectors → same speaker.
#    These vectors are clustered to group segments by speaker.
#
# Pipeline: Audio → VAD (find speech) → TitaNet (who's speaking) → Clustering (group by speaker)
VAD_MODEL = None
SPEAKER_MODEL = None

# NFA (Forced Alignment) - reuses PROTOVERB model via NeMo aligner_utils
# Provides word-level timestamps by aligning transcript to audio
# OUTPUT_TIMESTEP_DURATION is set after ASR model loads (from model config)
OUTPUT_TIMESTEP_DURATION = None

# Model paths - baked into Docker image
ASR_MODEL_PATH = os.environ.get("ASR_MODEL_PATH", "/app/models/asr/conformer_ctc_bpe.nemo")
PUNCTUATOR_MODEL_PATH = os.environ.get("PUNCTUATOR_MODEL_PATH", "/app/models/punctuator/nlp_tc_pc.nemo")

# Denormalizer path (Python package)
DENORMALIZER_PATH = os.environ.get("DENORMALIZER_PATH", "/app/Slovene_denormalizator")

# Maximum audio size (100MB)
MAX_AUDIO_SIZE = 100 * 1024 * 1024

# Model version identifier
MODEL_VERSION = "protoverb-1.0"


def load_asr_model():
    """
    Load PROTOVERB ASR model at container startup.

    Also sets OUTPUT_TIMESTEP_DURATION from model config for NFA alignment.
    """
    global ASR_MODEL, OUTPUT_TIMESTEP_DURATION

    if ASR_MODEL is not None:
        logger.info("ASR model already loaded, skipping")
        return

    logger.info(f"Loading PROTOVERB ASR model from {ASR_MODEL_PATH}")
    start_time = time.time()

    try:
        # Suppress NeMo's verbose warnings before loading
        from nemo.utils import logging as nemo_logging
        nemo_logging.setLevel(logging.ERROR)

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

        # Set OUTPUT_TIMESTEP_DURATION for NFA alignment (from model config)
        # This is the audio frame duration in seconds (~0.04s for PROTOVERB)
        cfg = ASR_MODEL.cfg
        OUTPUT_TIMESTEP_DURATION = cfg.preprocessor.window_stride
        logger.info(f"NFA timestep duration set to {OUTPUT_TIMESTEP_DURATION}s")

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
        # Add denormalizer to Python's import path
        # Python can only import modules from directories listed in sys.path.
        # The denormalizer is a standalone package (not pip-installed), so we
        # manually add its directory to sys.path to make "from denormalizer import ..."  work.
        # See: https://docs.python.org/3/library/sys.html#sys.path
        if DENORMALIZER_PATH not in sys.path:
            sys.path.insert(0, DENORMALIZER_PATH)

        # The denormalizer uses hardcoded relative paths internally (e.g., "data/rules.json").
        # These paths are relative to the current working directory (cwd), not to the package.
        # We temporarily change cwd to the denormalizer's directory so its relative paths resolve.
        #
        # Example problem without this:
        #   cwd = /app
        #   denormalizer tries to open "data/rules.json"
        #   Python looks for /app/data/rules.json → NOT FOUND!
        #
        # Solution: cd to /app/Slovene_denormalizator, import, then cd back.
        original_cwd = os.getcwd()
        os.chdir(DENORMALIZER_PATH)

        try:
            start_time = time.time()
            from denormalizer import denormalize as denorm_func
            DENORMALIZER = denorm_func
            load_time = time.time() - start_time
            logger.info(f"Denormalizer loaded successfully in {load_time:.2f}s")
        finally:
            # IMPORTANT: Always restore original cwd, even if import fails.
            # Other code may depend on the expected working directory.
            os.chdir(original_cwd)

    except Exception as e:
        logger.error(f"Failed to load denormalizer: {e}")
        # Don't raise - denormalization is optional


def load_diarization_models():
    """
    Load VAD and speaker embedding models for diarization.

    Models used:
    - MarbleNet: Voice Activity Detection (VAD)
    - TitaNet-Large: Speaker embeddings for clustering
    """
    global VAD_MODEL, SPEAKER_MODEL

    if VAD_MODEL is not None and SPEAKER_MODEL is not None:
        logger.info("Diarization models already loaded, skipping")
        return

    logger.info("Loading diarization models (VAD + TitaNet)")
    start_time = time.time()

    try:
        # Suppress NeMo's verbose warnings
        from nemo.utils import logging as nemo_logging
        nemo_logging.setLevel(logging.ERROR)

        # VAD model (MarbleNet)
        from nemo.collections.asr.models import EncDecClassificationModel
        VAD_MODEL = EncDecClassificationModel.from_pretrained("vad_marblenet")
        VAD_MODEL.eval()
        logger.info("VAD model (MarbleNet) loaded")

        # Speaker embedding model (TitaNet-Large)
        from nemo.collections.asr.models import EncDecSpeakerLabelModel
        SPEAKER_MODEL = EncDecSpeakerLabelModel.from_pretrained("titanet_large")
        SPEAKER_MODEL.eval()
        logger.info("Speaker model (TitaNet-Large) loaded")

        # Move to GPU if available
        cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
        if cuda_visible != "" and cuda_visible.lower() != "none":
            VAD_MODEL = VAD_MODEL.cuda()
            SPEAKER_MODEL = SPEAKER_MODEL.cuda()
            logger.info("Diarization models moved to GPU")
        else:
            logger.info("Diarization models running on CPU")

        load_time = time.time() - start_time
        logger.info(f"Diarization models loaded successfully in {load_time:.2f}s")

    except Exception as e:
        logger.error(f"Failed to load diarization models: {e}")
        raise


def load_models_parallel(
    need_asr: bool = True,
    need_punct: bool = True,
    need_denorm: bool = True,
    need_diarization: bool = False
):
    """
    Load required models with safe parallelism.

    NeMo models cannot be loaded in parallel due to shared module locks.
    Solution:
    - Phase 1: Load ASR + Denormalizer in parallel (Denormalizer is not NeMo)
    - Phase 2: Load Diarization models sequentially (NeMo ASR models)
    - Phase 3: Load Punctuator sequentially (NeMo NLP model)

    NFA (forced alignment) reuses the ASR model via NeMo aligner_utils,
    so no separate model loading is needed.
    """
    global ASR_MODEL, PUNCTUATOR_MODEL, DENORMALIZER, VAD_MODEL, SPEAKER_MODEL

    # Track what we're actually loading in this call
    loading = []
    if need_asr and ASR_MODEL is None:
        loading.append("ASR")
    if need_punct and PUNCTUATOR_MODEL is None:
        loading.append("Punctuator")
    if need_denorm and DENORMALIZER is None:
        loading.append("Denormalizer")
    if need_diarization and (VAD_MODEL is None or SPEAKER_MODEL is None):
        loading.append("Diarization")

    if not loading:
        return  # Everything already loaded

    start_time = time.time()

    # Phase 1: ASR + Denormalizer in parallel (Denormalizer is not NeMo, no conflict)
    phase1_loaders = []
    if need_asr and ASR_MODEL is None:
        phase1_loaders.append(("ASR", load_asr_model))
    if need_denorm and DENORMALIZER is None:
        phase1_loaders.append(("Denormalizer", load_denormalizer))

    if phase1_loaders:
        names = [name for name, _ in phase1_loaders]
        logger.info(f"Loading phase 1: {', '.join(names)}")

        if len(phase1_loaders) == 1:
            phase1_loaders[0][1]()
        else:
            with ThreadPoolExecutor(max_workers=len(phase1_loaders)) as executor:
                futures = [executor.submit(fn) for _, fn in phase1_loaders]
                wait(futures)

    # Phase 2: Diarization models (must be sequential - NeMo ASR models)
    if need_diarization and (VAD_MODEL is None or SPEAKER_MODEL is None):
        logger.info("Loading phase 2: Diarization")
        load_diarization_models()

    # Phase 3: Punctuator (must be sequential - NeMo NLP model)
    if need_punct and PUNCTUATOR_MODEL is None:
        logger.info("Loading phase 3: Punctuator")
        load_punctuator_model()

    load_time = time.time() - start_time
    logger.info(f"Models loaded in {load_time:.2f}s: {', '.join(loading)}")


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


def get_diarization_config(
    manifest_path: str,
    output_dir: str,
    num_speakers: int | None = None,
    max_speakers: int = 10
) -> Dict[str, Any]:
    """
    Create ClusteringDiarizer configuration.

    Uses 2-scale telephonic preset optimized for 1-2 speakers.

    Args:
        manifest_path: Path to manifest JSON file
        output_dir: Directory for RTTM output
        num_speakers: Known number of speakers (None for auto-detect)
        max_speakers: Maximum speakers for auto-detect

    Returns:
        OmegaConf configuration dict
    """
    # Determine device
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"

    config = {
        "name": "ClusteringDiarizer",
        "num_workers": 1,
        "sample_rate": 16000,
        "batch_size": 64,
        "device": device,  # Required by ClusteringDiarizer
        "verbose": True,
        "diarizer": {
            "manifest_filepath": manifest_path,
            "out_dir": output_dir,
            "oracle_vad": False,
            "collar": 0.25,
            "ignore_overlap": True,

            "vad": {
                "model_path": "vad_marblenet",
                "parameters": {
                    "window_length_in_sec": 0.15,
                    "shift_length_in_sec": 0.01,
                    "smoothing": "median",
                    "overlap": 0.5,
                    "onset": 0.8,
                    "offset": 0.6,
                    "min_duration_on": 0.1,
                    "min_duration_off": 0.1,
                    "pad_onset": 0.1,
                    "pad_offset": 0.1,
                    "postprocessing_params": {
                        "onset": 0.8,
                        "offset": 0.6,
                        "min_duration_on": 0.1,
                        "min_duration_off": 0.1,
                        "pad_onset": 0.1,
                        "pad_offset": 0.1
                    }
                }
            },

            "speaker_embeddings": {
                "model_path": "titanet_large",
                "parameters": {
                    # 2-scale telephonic preset (faster, good for 1-2 speakers)
                    "window_length_in_sec": [1.5, 1.0],
                    "shift_length_in_sec": [0.75, 0.5],
                    "multiscale_weights": [1, 1],
                    "save_embeddings": False
                }
            },

            "clustering": {
                "parameters": {
                    "oracle_num_speakers": num_speakers is not None,
                    "max_num_speakers": num_speakers if num_speakers else max_speakers,
                    "enhanced_count_thres": 80,
                    "max_rp_threshold": 0.25,
                    "sparse_search_volume": 30
                }
            }
        }
    }

    return config


def parse_rttm(rttm_path: str) -> List[Dict[str, Any]]:
    """
    Parse RTTM file to list of speaker segments.

    RTTM format: SPEAKER <file_id> <channel> <start> <duration> <NA> <NA> <speaker_id> <NA> <NA>

    Args:
        rttm_path: Path to RTTM file

    Returns:
        List of segments: [{"start": float, "duration": float, "speaker": str}, ...]
    """
    segments = []

    try:
        with open(rttm_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 8 and parts[0] == "SPEAKER":
                    segments.append({
                        "start": float(parts[3]),
                        "duration": float(parts[4]),
                        "speaker": parts[7]
                    })
    except Exception as e:
        logger.error(f"Failed to parse RTTM file {rttm_path}: {e}")
        return []

    # Sort by start time
    return sorted(segments, key=lambda s: s["start"])


def parse_ctm_file(ctm_path: str) -> List[Dict[str, Any]]:
    """
    Parse CTM file to list of word timestamps.

    CTM (Conversation Time Mark) format from NeMo Forced Aligner:
        <utt_id> <channel> <start_seconds> <duration_seconds> <word>

    Example:
        audio 1 0.320 0.240 pozdravljeni
        audio 1 0.560 0.180 kako
        audio 1 0.740 0.120 ste

    Args:
        ctm_path: Path to word-level CTM file

    Returns:
        List of words: [{"word": str, "start": float, "end": float}, ...]
    """
    words = []

    try:
        with open(ctm_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    start = float(parts[2])
                    duration = float(parts[3])
                    word = parts[4]
                    words.append({
                        "word": word,
                        "start": start,
                        "end": start + duration
                    })
    except Exception as e:
        logger.error(f"Failed to parse CTM file {ctm_path}: {e}")
        return []

    return words


def run_diarization(
    audio_path: str,
    num_speakers: int | None = None,
    max_speakers: int = 10
) -> List[Dict[str, Any]]:
    """
    Run speaker diarization on audio file.

    Args:
        audio_path: Path to audio file (WAV format)
        num_speakers: Known number of speakers (None for auto-detect)
        max_speakers: Maximum speakers for auto-detect

    Returns:
        List of speaker segments: [{"start": float, "duration": float, "speaker": str}, ...]
    """
    global VAD_MODEL, SPEAKER_MODEL

    if VAD_MODEL is None or SPEAKER_MODEL is None:
        raise RuntimeError("Diarization models not loaded")

    import json
    from omegaconf import OmegaConf
    from nemo.collections.asr.models import ClusteringDiarizer

    # Create temp directories for manifest and output
    temp_dir = tempfile.mkdtemp(prefix="diarization_")
    manifest_path = os.path.join(temp_dir, "manifest.json")
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Create manifest file
        manifest = {
            "audio_filepath": audio_path,
            "offset": 0,
            "duration": None,
            "label": "infer",
            "text": "-",
            "num_speakers": num_speakers,
            "rttm_filepath": None,
            "uem_filepath": None
        }

        with open(manifest_path, "w") as f:
            json.dump(manifest, f)
            f.write("\n")

        logger.info(f"Running diarization on {audio_path} (num_speakers={num_speakers}, max={max_speakers})")
        start_time = time.time()

        # Get config and create diarizer
        config_dict = get_diarization_config(
            manifest_path=manifest_path,
            output_dir=output_dir,
            num_speakers=num_speakers,
            max_speakers=max_speakers
        )
        config = OmegaConf.create(config_dict)

        # Run diarization
        diarizer = ClusteringDiarizer(cfg=config)
        diarizer.diarize()

        diarization_time = time.time() - start_time
        logger.info(f"Diarization complete in {diarization_time:.2f}s")

        # Find and parse RTTM output
        # NeMo outputs RTTM files to pred_rttms/ subdirectory
        pred_rttms_dir = os.path.join(output_dir, "pred_rttms")

        # Check both locations (direct and pred_rttms subdirectory)
        rttm_files = []
        if os.path.exists(pred_rttms_dir):
            rttm_files = [os.path.join(pred_rttms_dir, f)
                         for f in os.listdir(pred_rttms_dir) if f.endswith(".rttm")]

        if not rttm_files:
            # Fallback: check output_dir directly
            rttm_files = [os.path.join(output_dir, f)
                         for f in os.listdir(output_dir) if f.endswith(".rttm")]

        if not rttm_files:
            # Debug: list what files were actually created
            logger.warning(f"No RTTM file generated. Output dir contents: {os.listdir(output_dir)}")
            if os.path.exists(pred_rttms_dir):
                logger.warning(f"pred_rttms contents: {os.listdir(pred_rttms_dir)}")
            return []

        rttm_path = rttm_files[0]
        logger.info(f"Found RTTM file: {rttm_path}")
        segments = parse_rttm(rttm_path)

        logger.info(f"Found {len(segments)} speaker segments")
        return segments

    except Exception as e:
        logger.error(f"Diarization failed: {e}")
        return []

    finally:
        # Cleanup temp directory
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception:
            pass


def run_forced_alignment(
    audio_path: str,
    transcript: str,
    segment_start: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Run forced alignment to get word-level timestamps using NeMo Forced Aligner.

    ## What is Forced Alignment?

    Forced alignment answers: "Given audio and its transcript, WHEN was each word spoken?"

    Unlike ASR (which discovers WHAT was said), forced alignment already knows the text
    and just needs to find WHERE each word occurs in the audio timeline.

    ## How it works (CTC + Viterbi)

    PROTOVERB is a CTC (Connectionist Temporal Classification) model:
    - CTC outputs a probability distribution over characters for each audio frame (~40ms)
    - Example: frame 15 might be 80% "a", 10% "b", 10% blank
    - During ASR, we find the most likely CHARACTER sequence
    - During alignment, we already KNOW the characters and find their most likely TIMES

    Viterbi algorithm finds the optimal alignment:
    - Dynamic programming algorithm that finds the most probable path through the CTC output
    - Given transcript "hello", it finds which frames most likely correspond to h-e-l-l-o
    - Output: frame ranges for each character, aggregated into word timestamps

    ## Implementation

    Uses NeMo's aligner_utils Python API which reuses the PROTOVERB ASR model
    for alignment. No separate model needed (saves ~2GB memory vs MMS approach).
    Apache 2.0 licensed (commercial use allowed).

    Args:
        audio_path: Path to audio file (WAV format)
        transcript: Full transcript text from ASR
        segment_start: Offset to add to all timestamps (for segment-based processing)

    Returns:
        List of word timestamps: [{"word": str, "start": float, "end": float}, ...]
        Empty list if alignment fails (falls back to proportional splitting).
    """
    global ASR_MODEL, OUTPUT_TIMESTEP_DURATION

    if ASR_MODEL is None:
        logger.warning("ASR model not loaded, skipping forced alignment")
        return []

    if not transcript or not transcript.strip():
        logger.warning("Empty transcript, skipping forced alignment")
        return []

    try:
        import torch
        from nemo_compat.aligner_utils import (
            get_batch_variables,
            viterbi_decoding,
            add_t_start_end_to_utt_obj,
        )

        logger.info(f"Running NFA alignment on {audio_path} ({len(transcript.split())} words)")
        start_time = time.time()

        # Step 1: Get CTC log probabilities using PROTOVERB model
        # Note: Both audio and gt_text_batch must be lists of same length
        log_probs, y, T, U, utt_objs, timestep_duration = get_batch_variables(
            audio=[audio_path],
            model=ASR_MODEL,
            gt_text_batch=[transcript],
            output_timestep_duration=OUTPUT_TIMESTEP_DURATION,
        )

        # Step 2: Viterbi alignment to find optimal character-to-frame mapping
        device = "cuda" if torch.cuda.is_available() else "cpu"
        alignments = viterbi_decoding(log_probs, y, T, U, viterbi_device=device)

        # Step 3: Map frame alignments to word timestamps
        utt_obj = add_t_start_end_to_utt_obj(
            utt_obj=utt_objs[0],
            alignment_utt=alignments[0],
            output_timestep_duration=timestep_duration,
        )

        # Step 4: Extract words with timestamps
        # Utterance.segments_and_tokens contains Segment and Token objects
        # Segment.words_and_tokens contains Word and Token objects
        from nemo_compat.aligner_utils import Segment, Word

        words = []
        for item in utt_obj.segments_and_tokens:
            if isinstance(item, Segment):
                for word_item in item.words_and_tokens:
                    if isinstance(word_item, Word) and word_item.t_start is not None:
                        words.append({
                            "word": word_item.text,
                            "start": round(word_item.t_start + segment_start, 3),
                            "end": round(word_item.t_end + segment_start, 3),
                        })

        alignment_time = time.time() - start_time
        logger.info(f"NFA alignment complete in {alignment_time:.2f}s: {len(words)} words")
        return words

    except ImportError as e:
        logger.error(f"NeMo aligner_utils not available: {e}")
        return []

    except Exception as e:
        logger.error(f"Forced alignment failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []  # Fallback to proportional splitting


def merge_words_with_speakers(
    words_with_timestamps: List[Dict[str, Any]],
    speaker_segments: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge word-level timestamps with speaker diarization segments.

    Uses word midpoint to determine speaker assignment - the speaker who
    is active at the midpoint of a word "owns" that word.

    This is much more accurate than proportional splitting because:
    - Each word is assigned based on its actual timing
    - Different speech rates are handled correctly
    - Speaker boundaries align with actual word boundaries

    Args:
        words_with_timestamps: List from run_forced_alignment()
            [{"word": str, "start": float, "end": float}, ...]
        speaker_segments: List from run_diarization()
            [{"start": float, "duration": float, "speaker": str}, ...]

    Returns:
        List of segments with word-level detail:
        [{
            "id": int,
            "start": float,
            "end": float,
            "text": str,
            "speaker": str,
            "words": [{"word": str, "start": float, "end": float}, ...]
        }, ...]
    """
    if not words_with_timestamps:
        return []

    if not speaker_segments:
        # No diarization - return all words as single segment without speaker
        all_text = " ".join(w["word"] for w in words_with_timestamps)
        return [{
            "id": 0,
            "start": words_with_timestamps[0]["start"],
            "end": words_with_timestamps[-1]["end"],
            "text": all_text,
            "speaker": None,
            "words": words_with_timestamps
        }]

    # Sort speaker segments by start time
    sorted_segments = sorted(speaker_segments, key=lambda s: s["start"])

    # Map speaker IDs to friendly names (Speaker 1, Speaker 2, ...)
    speaker_map = {}
    speaker_counter = 1

    def get_speaker_for_time(t: float) -> str | None:
        """
        Find which speaker is active at time t.

        First tries exact match (time falls within a segment).
        If no exact match, falls back to nearest segment by time distance.
        This handles gaps between diarization segments where words may fall.
        """
        nonlocal speaker_counter  # Must be declared before any use

        def get_or_create_speaker_name(speaker_id: str) -> str:
            """Map internal speaker ID to friendly name (Speaker 1, Speaker 2, ...)"""
            nonlocal speaker_counter
            if speaker_id not in speaker_map:
                speaker_map[speaker_id] = f"Speaker {speaker_counter}"
                speaker_counter += 1
            return speaker_map[speaker_id]

        # First: try exact match (word falls within a speaker segment)
        for seg in sorted_segments:
            seg_start = seg["start"]
            seg_end = seg_start + seg["duration"]
            if seg_start <= t <= seg_end:
                return get_or_create_speaker_name(seg["speaker"])

        # Fallback: find closest segment by time distance
        # This handles words that fall in gaps between speaker segments
        if sorted_segments:
            def distance_to_segment(seg):
                seg_start = seg["start"]
                seg_end = seg_start + seg["duration"]
                if t < seg_start:
                    return seg_start - t  # Time is before segment
                else:
                    return t - seg_end  # Time is after segment

            closest_seg = min(sorted_segments, key=distance_to_segment)
            return get_or_create_speaker_name(closest_seg["speaker"])

        return None

    # Assign speaker to each word based on midpoint
    words_with_speakers = []
    for word in words_with_timestamps:
        midpoint = (word["start"] + word["end"]) / 2
        speaker = get_speaker_for_time(midpoint)
        words_with_speakers.append({
            **word,
            "speaker": speaker
        })

    # Group consecutive words by speaker into segments
    result = []
    current_segment_words = []
    current_speaker = None

    for word in words_with_speakers:
        if word["speaker"] != current_speaker:
            # Flush previous segment
            if current_segment_words:
                result.append({
                    "id": len(result),
                    "start": current_segment_words[0]["start"],
                    "end": current_segment_words[-1]["end"],
                    "text": " ".join(w["word"] for w in current_segment_words),
                    "speaker": current_speaker,
                    "words": [{"word": w["word"], "start": w["start"], "end": w["end"]}
                              for w in current_segment_words]
                })
            current_speaker = word["speaker"]
            current_segment_words = [word]
        else:
            current_segment_words.append(word)

    # Flush final segment
    if current_segment_words:
        result.append({
            "id": len(result),
            "start": current_segment_words[0]["start"],
            "end": current_segment_words[-1]["end"],
            "text": " ".join(w["word"] for w in current_segment_words),
            "speaker": current_speaker,
            "words": [{"word": w["word"], "start": w["start"], "end": w["end"]}
                      for w in current_segment_words]
        })

    return result


def format_transcript_with_speakers(segments: List[Dict[str, Any]]) -> str:
    """
    Format segments as speaker-labeled transcript text.

    Consecutive segments from the same speaker are merged together,
    producing a clean dialogue format where each speaker turn appears once.

    Args:
        segments: List of segments from merge_words_with_speakers().
            Each segment should have 'speaker' and 'text' keys.

    Returns:
        Formatted string with speaker labels, e.g.:
        "Speaker 1: Hello, how are you? Speaker 2: I'm doing well, thanks."

    Example:
        >>> segments = [
        ...     {"speaker": "Speaker 1", "text": "Hello."},
        ...     {"speaker": "Speaker 1", "text": "How are you?"},
        ...     {"speaker": "Speaker 2", "text": "I'm fine."},
        ... ]
        >>> format_transcript_with_speakers(segments)
        "Speaker 1: Hello. How are you? Speaker 2: I'm fine."
    """
    if not segments:
        return ""

    parts = []
    current_speaker = None
    current_text = []

    for seg in segments:
        speaker = seg.get("speaker")
        text = seg.get("text", "")

        if speaker != current_speaker:
            # Flush previous speaker's text
            if current_text and current_speaker:
                parts.append(f"{current_speaker}: {' '.join(current_text)}")
            current_speaker = speaker
            current_text = [text] if text else []
        else:
            if text:
                current_text.append(text)

    # Flush final speaker's text
    if current_text and current_speaker:
        parts.append(f"{current_speaker}: {' '.join(current_text)}")

    return " ".join(parts)


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


def extract_audio_segment(
    audio_path: str,
    start: float,
    end: float,
    padding_before: float = 0.0,
    padding_after: float = 0.0
) -> tuple:
    """
    Extract audio segment to a temporary file with optional context padding.

    Uses soundfile for efficient audio slicing without re-encoding.
    Padding adds extra audio before/after for ASR context, which improves
    transcription quality on short segments.

    Args:
        audio_path: Path to source audio file
        start: Start time in seconds (of the actual segment)
        end: End time in seconds (of the actual segment)
        padding_before: Extra audio to include before start (seconds)
        padding_after: Extra audio to include after end (seconds)

    Returns:
        Tuple of (path to temp file, actual_start, actual_end) where
        actual_start/end reflect the padding applied (clamped to file bounds)
    """
    import soundfile as sf

    # Read audio file
    audio_data, sample_rate = sf.read(audio_path)
    total_duration = len(audio_data) / sample_rate

    # Apply padding (clamped to file bounds)
    padded_start = max(0, start - padding_before)
    padded_end = min(total_duration, end + padding_after)

    # Calculate sample indices
    start_sample = int(padded_start * sample_rate)
    end_sample = int(padded_end * sample_rate)

    # Clamp to valid range
    start_sample = max(0, start_sample)
    end_sample = min(len(audio_data), end_sample)

    # Extract segment
    segment_data = audio_data[start_sample:end_sample]

    # Write to temp file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, segment_data, sample_rate)
        return tmp.name, padded_start, padded_end


# Configuration for segment processing
MIN_SEGMENT_FOR_ASR = 3.0  # Merge segments shorter than this (seconds)
MAX_SEGMENT_FOR_ASR = 30.0  # Don't merge if result would exceed this (seconds)
CONTEXT_PADDING = 0.5  # Add this much audio before/after for ASR context (seconds)
MIN_SEGMENT_FOR_NFA = 2.0  # Skip NFA for segments shorter than this (seconds)


def merge_short_segments_for_asr(
    segments: List[Dict[str, Any]],
    min_duration: float = MIN_SEGMENT_FOR_ASR,
    max_duration: float = MAX_SEGMENT_FOR_ASR
) -> List[Dict[str, Any]]:
    """
    Merge adjacent short segments from the same speaker BEFORE running ASR.

    PROTOVERB ASR quality degrades significantly on very short segments (<3s)
    because it lacks acoustic context. This function merges adjacent same-speaker
    segments to ensure each segment has enough context for quality transcription.

    Constraints:
    - Only merges same-speaker segments
    - Only merges if at least one segment is < min_duration
    - Never creates segments > max_duration (prevents NFA slowdown)

    Args:
        segments: Raw diarization segments from run_diarization()
        min_duration: Minimum segment duration in seconds (default: 3.0)
        max_duration: Maximum segment duration in seconds (default: 30.0)

    Returns:
        List of merged segments where short same-speaker segments are combined
    """
    if not segments:
        return []

    logger.info(
        f"Pre-merging short segments: {len(segments)} segments, "
        f"min_duration={min_duration}s, max_duration={max_duration}s"
    )

    merged = []
    current = None

    for seg in segments:
        duration = seg.get("duration", 0)
        speaker = seg["speaker"]

        if current is None:
            # First segment
            current = {
                "start": seg["start"],
                "duration": duration,
                "speaker": speaker
            }
        elif speaker == current["speaker"]:
            # Same speaker - check if we should merge
            new_end = seg["start"] + duration
            potential_duration = new_end - current["start"]

            # Only merge if:
            # 1. At least one segment is short (< min_duration)
            # 2. Result won't exceed max_duration
            should_merge = (
                (duration < min_duration or current["duration"] < min_duration)
                and potential_duration <= max_duration
            )

            if should_merge:
                current["duration"] = potential_duration
            else:
                # Can't merge - flush current and start new
                merged.append(current)
                current = {
                    "start": seg["start"],
                    "duration": duration,
                    "speaker": speaker
                }
        else:
            # Different speaker - flush current and start new
            merged.append(current)
            current = {
                "start": seg["start"],
                "duration": duration,
                "speaker": speaker
            }

    # Don't forget the last segment
    if current:
        merged.append(current)

    logger.info(
        f"Pre-merge complete: {len(segments)} -> {len(merged)} segments "
        f"({len(segments) - len(merged)} merged)"
    )

    return merged


def process_diarization_segment(
    audio_path: str,
    segment: Dict[str, Any],
    segment_index: int
) -> Dict[str, Any]:
    """
    Process a single diarization segment: extract audio, run ASR, run NFA.

    This function is designed to be run in parallel for each segment.

    Features:
    - Context padding: Adds CONTEXT_PADDING seconds before/after for ASR quality
    - Skips NFA on tiny segments (<MIN_SEGMENT_FOR_NFA) to reduce overhead

    Args:
        audio_path: Path to full audio file
        segment: Diarization segment {"start": float, "duration": float, "speaker": str}
        segment_index: Index of this segment (for logging)

    Returns:
        Processed segment with text and word timestamps:
        {
            "id": int,
            "start": float,
            "end": float,
            "speaker": str,
            "text": str,
            "words": [{"word": str, "start": float, "end": float}, ...]
        }
    """
    start = segment["start"]
    duration = segment["duration"]
    end = start + duration
    speaker = segment["speaker"]

    segment_audio_path = None
    try:
        # Extract audio segment with context padding for better ASR quality
        segment_audio_path, padded_start, padded_end = extract_audio_segment(
            audio_path, start, end,
            padding_before=CONTEXT_PADDING,
            padding_after=CONTEXT_PADDING
        )

        # Run ASR on segment (with padded audio for context)
        segment_text = transcribe_audio(segment_audio_path)

        if not segment_text.strip():
            logger.debug(f"Segment {segment_index}: empty transcription")
            return {
                "id": segment_index,
                "start": start,
                "end": end,
                "speaker": speaker,
                "text": "",
                "words": []
            }

        words = []

        # Skip NFA on very short segments (not worth the overhead)
        if duration < MIN_SEGMENT_FOR_NFA:
            logger.debug(
                f"Segment {segment_index}: skipping NFA (duration={duration:.1f}s < "
                f"{MIN_SEGMENT_FOR_NFA}s threshold)"
            )
        else:
            # Run NFA on segment for word-level timestamps
            word_timestamps = run_forced_alignment(segment_audio_path, segment_text)

            # Adjust word timestamps to absolute time
            # NFA timestamps are relative to padded audio, so add padded_start offset
            for w in word_timestamps:
                words.append({
                    "word": w["word"],
                    "start": round(padded_start + w["start"], 2),
                    "end": round(padded_start + w["end"], 2)
                })

        logger.debug(
            f"Segment {segment_index} [{start:.1f}s-{end:.1f}s] {speaker}: "
            f"{len(segment_text)} chars, {len(words)} words"
        )

        return {
            "id": segment_index,
            "start": start,
            "end": end,
            "speaker": speaker,
            "text": segment_text,
            "words": words
        }

    except Exception as e:
        logger.error(f"Failed to process segment {segment_index}: {e}")
        return {
            "id": segment_index,
            "start": start,
            "end": end,
            "speaker": speaker,
            "text": "",
            "words": [],
            "error": str(e)
        }

    finally:
        # Cleanup temp file
        if segment_audio_path:
            try:
                os.unlink(segment_audio_path)
            except Exception:
                pass


def process_segments_parallel(
    audio_path: str,
    segments: List[Dict[str, Any]],
    max_workers: int = 4
) -> List[Dict[str, Any]]:
    """
    Process all diarization segments in parallel.

    Runs ASR + NFA on each segment concurrently using ThreadPoolExecutor.

    Args:
        audio_path: Path to full audio file
        segments: List of diarization segments from run_diarization()
        max_workers: Maximum parallel workers (default: 4)

    Returns:
        List of processed segments with text and word timestamps,
        sorted by start time
    """
    if not segments:
        return []

    logger.info(f"Processing {len(segments)} segments in parallel (max_workers={max_workers})")
    start_time = time.time()

    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all segments for processing
        futures = {
            executor.submit(
                process_diarization_segment,
                audio_path,
                segment,
                i
            ): i for i, segment in enumerate(segments)
        }

        # Collect results as they complete
        for future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                segment_idx = futures[future]
                logger.error(f"Segment {segment_idx} failed: {e}")

    # Sort by start time
    results.sort(key=lambda s: s["start"])

    # Reassign IDs after sorting
    for i, seg in enumerate(results):
        seg["id"] = i

    elapsed = time.time() - start_time
    total_words = sum(len(s.get("words", [])) for s in results)
    logger.info(
        f"Parallel processing complete in {elapsed:.1f}s: "
        f"{len(results)} segments, {total_words} words"
    )

    return results


def merge_consecutive_speaker_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge consecutive segments from the same speaker.

    Diarization often produces many small segments. This merges consecutive
    segments from the same speaker into longer segments for cleaner output.

    Args:
        segments: List of processed segments with speaker labels

    Returns:
        List of merged segments where consecutive same-speaker segments are combined
    """
    if not segments:
        return []

    # Map internal speaker IDs to friendly names
    speaker_map = {}
    speaker_counter = 1

    def get_speaker_name(speaker_id: str) -> str:
        nonlocal speaker_counter
        if speaker_id not in speaker_map:
            speaker_map[speaker_id] = f"Speaker {speaker_counter}"
            speaker_counter += 1
        return speaker_map[speaker_id]

    merged = []
    current = None

    for seg in segments:
        speaker_name = get_speaker_name(seg["speaker"])

        if current is None:
            # First segment
            current = {
                "id": 0,
                "start": seg["start"],
                "end": seg["end"],
                "speaker": speaker_name,
                "text": seg["text"],
                "words": list(seg.get("words", []))
            }
        elif speaker_name == current["speaker"]:
            # Same speaker - merge
            current["end"] = seg["end"]
            if seg["text"]:
                current["text"] = (current["text"] + " " + seg["text"]).strip()
            current["words"].extend(seg.get("words", []))
        else:
            # Different speaker - flush current and start new
            merged.append(current)
            current = {
                "id": len(merged),
                "start": seg["start"],
                "end": seg["end"],
                "speaker": speaker_name,
                "text": seg["text"],
                "words": list(seg.get("words", []))
            }

    # Flush final segment
    if current:
        merged.append(current)

    return merged


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
            - enable_diarization: Whether to identify speakers (default: False)
            - speaker_count: Known number of speakers, null for auto-detect (default: null)
            - max_speakers: Maximum speakers for auto-detect (default: 10)

    Returns:
        dict with:
            - text: Final processed text (with speaker labels if diarization enabled)
            - raw_text: Original ASR output (no punctuation/denormalization)
            - processing_time: Time taken in seconds
            - pipeline: List of processing steps applied
            - model_version: Model version identifier
            - diarization_applied: Whether diarization was applied
            - speaker_count_detected: Number of speakers detected (if diarization)
            - segments: List of segments with speaker labels (if diarization)
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

    # Diarization options (default: disabled)
    do_diarization = job_input.get("enable_diarization", False)
    speaker_count = job_input.get("speaker_count", None)  # None = auto-detect
    max_speakers = job_input.get("max_speakers", 10)

    # Validate speaker_count
    if speaker_count is not None:
        if not isinstance(speaker_count, int) or speaker_count < 1 or speaker_count > 20:
            logger.warning(f"Invalid speaker_count '{speaker_count}', using auto-detect")
            speaker_count = None

    # Validate max_speakers
    if not isinstance(max_speakers, int) or max_speakers < 1 or max_speakers > 20:
        logger.warning(f"Invalid max_speakers '{max_speakers}', using 10")
        max_speakers = 10

    # Load required models (parallel if multiple needed)
    try:
        load_models_parallel(
            need_asr=True,
            need_punct=do_punctuate,
            need_denorm=do_denormalize,
            need_diarization=do_diarization
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
        logger.info(
            f"Options: punctuate={do_punctuate}, denormalize={do_denormalize}, "
            f"style={denormalize_style}, diarization={do_diarization}, "
            f"speaker_count={speaker_count}, max_speakers={max_speakers}"
        )

        # Run ASR and diarization
        raw_text = ""
        segments = []
        diarization_applied = False
        nfa_applied = False

        if do_diarization:
            # ================================================================
            # DIARIZE-FIRST ARCHITECTURE
            # ================================================================
            # This architecture solves the "dropped words" problem where ASR
            # on long audio would miss utterances during speaker transitions.
            #
            # Flow:
            #   1. Diarization (full audio) → speaker segments with timestamps
            #   2. For each segment in parallel:
            #      - Extract segment audio
            #      - ASR on segment → text
            #      - NFA on segment → word timestamps
            #   3. Merge consecutive same-speaker segments
            #   4. Apply punctuation/denormalization per segment
            #
            # Why this works better:
            #   - ASR on short segments (5-30s) captures words that would be
            #     dropped on full 3-5 minute audio
            #   - NFA is faster and more accurate on short segments
            #   - Each segment is already attributed to a speaker
            # ================================================================

            # Phase 1: Run diarization first on full audio
            logger.info("Phase 1: Running diarization on full audio")
            speaker_segments = run_diarization(tmp_path, speaker_count, max_speakers)

            if not speaker_segments:
                logger.warning("Diarization returned no segments - falling back to ASR only")
                raw_text = transcribe_audio(tmp_path)
                pipeline_steps.append("asr")
                logger.info(f"ASR complete: {len(raw_text)} chars")
            else:
                pipeline_steps.append("diarize")
                diarization_applied = True
                logger.info(f"Diarization complete: {len(speaker_segments)} raw segments")

                # Phase 1.5: Pre-merge short same-speaker segments for better ASR context
                # PROTOVERB quality degrades on very short segments (<3s)
                merged_for_asr = merge_short_segments_for_asr(
                    speaker_segments,
                    min_duration=MIN_SEGMENT_FOR_ASR
                )

                # Phase 2: Process each segment in parallel (ASR + NFA per segment)
                logger.info("Phase 2: Processing segments in parallel (ASR + NFA per segment)")
                processed_segments = process_segments_parallel(
                    tmp_path,
                    merged_for_asr,  # Use pre-merged segments
                    max_workers=4
                )
                pipeline_steps.append("asr")
                pipeline_steps.append("align")
                nfa_applied = True

                # Phase 3: Merge consecutive segments from same speaker
                logger.info("Phase 3: Merging consecutive speaker segments")
                segments = merge_consecutive_speaker_segments(processed_segments)
                logger.info(f"Merged into {len(segments)} speaker turns")

                # Collect raw text (for backward compatibility)
                raw_text = " ".join(seg["text"] for seg in segments if seg.get("text"))

        else:
            # ASR only (no diarization)
            raw_text = transcribe_audio(tmp_path)
            pipeline_steps.append("asr")
            logger.info(f"ASR complete: {len(raw_text)} chars")

        # Process text based on diarization results
        text = raw_text
        speaker_count_detected = 0

        if diarization_applied and segments:
            # Count unique speakers
            unique_speakers = set(seg.get("speaker") for seg in segments if seg.get("speaker"))
            speaker_count_detected = len(unique_speakers)

            # Apply punctuation and denormalization per segment
            logger.info("Phase 4: Applying punctuation and denormalization per segment")
            for seg in segments:
                seg_text = seg["text"]

                if do_punctuate and PUNCTUATOR_MODEL is not None:
                    seg_text = apply_punctuation(seg_text)

                if do_denormalize and DENORMALIZER is not None:
                    seg_text = apply_denormalization(seg_text, style=denormalize_style)

                seg["text"] = seg_text

            if do_punctuate and PUNCTUATOR_MODEL is not None:
                pipeline_steps.append("punctuate")
            if do_denormalize and DENORMALIZER is not None:
                pipeline_steps.append("denormalize")

            # Format combined text with speaker labels
            text = format_transcript_with_speakers(segments)
            logger.info(f"Final output: {speaker_count_detected} speakers, {len(text)} chars")
        else:
            # No diarization - apply punctuation and denormalization to full text
            if do_punctuate and PUNCTUATOR_MODEL is not None:
                text = apply_punctuation(text)
                pipeline_steps.append("punctuate")
                logger.info(f"Punctuation complete: {len(text)} chars")

            if do_denormalize and DENORMALIZER is not None:
                text = apply_denormalization(text, style=denormalize_style)
                pipeline_steps.append("denormalize")
                logger.info(f"Denormalization complete: {len(text)} chars")

        processing_time = time.time() - start_time

        logger.info(
            f"Processing complete: pipeline={pipeline_steps}, "
            f"time={processing_time:.2f}s, output={len(text)} chars"
        )

        result = {
            "text": text,
            "raw_text": raw_text,
            "processing_time": processing_time,
            "pipeline": pipeline_steps,
            "model_version": MODEL_VERSION,
            "diarization_applied": diarization_applied,
        }

        # Add diarization-specific fields
        if diarization_applied:
            result["speaker_count_detected"] = speaker_count_detected
            result["segments"] = segments
            # Indicates NFA was used for precise word-level timestamps
            result["word_level_timestamps"] = nfa_applied

        return result

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
