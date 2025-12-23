"""
RunPod serverless handler for Slovenian ASR with NLP pipeline and speaker diarization.

This handler runs on RunPod serverless GPU and processes audio transcription
requests using the PROTOVERB NeMo model with optional punctuation, denormalization,
and speaker diarization.

Pipeline:
    Without diarization:
        Audio -> ASR (PROTOVERB) -> Punctuation (optional) -> Denormalization (optional)

    With diarization:
        Audio -> ASR (PROTOVERB) ─┬─> NFA alignment ──┬─> Merge -> Punctuation -> Denormalization
                                  │                      │                                    │
                                  └─> Diarization  ────────────────┘

    NFA (NeMo Forced Aligner) provides word-level timestamps for precise speaker assignment.
    If NFA fails, diarization is skipped.

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
    """
    global ASR_MODEL

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
    transcript: str
) -> List[Dict[str, Any]]:
    """
    Run forced alignment to get word-level timestamps.

    ## What is Forced Alignment?

    Forced alignment answers: "Given audio and its transcript, WHEN was each word spoken?"

    Unlike ASR (which discovers WHAT was said), forced alignment already knows the text
    and just needs to find WHERE each word occurs in the audio timeline.

    ## How it works (CTC + Viterbi)

    PROTOVERB is a CTC (Connectionist Temporal Classification) model:
    - CTC outputs a probability distribution over characters for each audio frame (~20ms)
    - Example: frame 15 might be 80% "a", 10% "b", 10% blank
    - During ASR, we find the most likely CHARACTER sequence
    - During alignment, we already KNOW the characters and find their most likely TIMES

    Viterbi algorithm finds the optimal alignment:
    - Dynamic programming algorithm that finds the most probable path through the CTC output
    - Given transcript "hello", it finds which frames most likely correspond to h-e-l-l-o
    - Output: frame ranges for each character, aggregated into word timestamps

    ## Implementation

    Uses ctc-forced-aligner library which provides a programmatic Python API
    for CTC-based forced alignment. This is much simpler than NeMo's CLI-based
    align.py tool and uses 5X less memory than TorchAudio's API.

    Args:
        audio_path: Path to audio file (WAV format)
        transcript: Full transcript text from ASR

    Returns:
        List of word timestamps: [{"word": str, "start": float, "end": float}, ...]
        Empty list if alignment fails (speaker attribution will be skipped).
    """
    global ASR_MODEL

    if ASR_MODEL is None:
        logger.error("ASR model not loaded, cannot run forced alignment")
        return []

    if not transcript or not transcript.strip():
        logger.warning("Empty transcript, skipping forced alignment")
        return []

    try:
        logger.info(f"Running forced alignment on {audio_path} ({len(transcript.split())} words)")
        start_time = time.time()

        # Use ctc-forced-aligner library
        # This provides a clean Python API for forced alignment with CTC models
        try:
            import torch
            from ctc_forced_aligner import (
                load_audio,
                load_alignment_model,
                generate_emissions,
                preprocess_text,
                get_alignments,
                get_spans,
                postprocess_results,
            )

            # Determine device
            device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.float16 if device == "cuda" else torch.float32

            # Load alignment model (uses pretrained multilingual Wav2Vec2/MMS)
            # This model is separate from PROTOVERB but works well for Slovenian
            alignment_model, alignment_tokenizer = load_alignment_model(
                device,
                dtype=dtype,
            )

            # Load and process audio
            audio_waveform = load_audio(
                audio_path,
                alignment_model.dtype,
                alignment_model.device
            )

            # Generate emissions (log probabilities) from alignment model
            emissions, stride = generate_emissions(
                alignment_model,
                audio_waveform,
                batch_size=16
            )

            # Preprocess text (tokenize and prepare for alignment)
            # romanize=False since Slovenian uses Latin alphabet
            tokens_starred, text_starred = preprocess_text(
                transcript,
                romanize=False,
                language="slv"  # ISO 639-3 code for Slovenian
            )

            # Get alignments using Viterbi algorithm
            segments, scores, blank_token = get_alignments(
                emissions,
                tokens_starred,
                alignment_tokenizer
            )

            # Get word-level spans
            spans = get_spans(tokens_starred, segments, blank_token)

            # Post-process results to get clean word timestamps
            word_timestamps = postprocess_results(
                text_starred,
                spans,
                stride,
                scores
            )

            # Convert to our expected format
            words = []
            for item in word_timestamps:
                words.append({
                    "word": item["text"],
                    "start": item["start"],
                    "end": item["end"]
                })

            alignment_time = time.time() - start_time
            logger.info(f"Forced alignment complete in {alignment_time:.2f}s: {len(words)} words")
            return words

        except ImportError as e:
            logger.warning(f"ctc-forced-aligner not available: {e}")
            logger.warning("Install with: pip install ctc-forced-aligner")
            return []

    except Exception as e:
        logger.error(f"Forced alignment failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


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
        """Find which speaker is active at time t."""
        nonlocal speaker_counter  # Must be declared before any use
        for seg in sorted_segments:
            seg_start = seg["start"]
            seg_end = seg_start + seg["duration"]
            if seg_start <= t <= seg_end:
                speaker_id = seg["speaker"]
                if speaker_id not in speaker_map:
                    speaker_map[speaker_id] = f"Speaker {speaker_counter}"
                    speaker_counter += 1
                return speaker_map[speaker_id]
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

        # Run ASR and diarization (parallel if diarization enabled)
        raw_text = ""
        speaker_segments = []
        word_timestamps = []
        diarization_applied = False
        nfa_applied = False

        if do_diarization:
            # Phase 1: Run ASR first (NFA needs transcript as input)
            raw_text = transcribe_audio(tmp_path)
            pipeline_steps.append("asr")
            logger.info(f"ASR complete: {len(raw_text)} chars")

            # Phase 2: Run NFA and diarization in parallel
            # Both need only audio + transcript, so they can run concurrently
            logger.info("Running NFA alignment and diarization in parallel")
            with ThreadPoolExecutor(max_workers=2) as executor:
                nfa_future = executor.submit(run_forced_alignment, tmp_path, raw_text)
                diar_future = executor.submit(
                    run_diarization, tmp_path, speaker_count, max_speakers
                )

                # Wait for both to complete
                word_timestamps = nfa_future.result()
                speaker_segments = diar_future.result()

            if word_timestamps:
                pipeline_steps.append("align")
                nfa_applied = True
                logger.info(f"NFA alignment complete: {len(word_timestamps)} words")
            else:
                logger.warning("NFA alignment failed - speaker attribution will be skipped")

            if speaker_segments:
                pipeline_steps.append("diarize")
                diarization_applied = True
                logger.info(f"Diarization complete: {len(speaker_segments)} segments")
            else:
                logger.warning("Diarization returned no segments")
        else:
            # ASR only
            raw_text = transcribe_audio(tmp_path)
            pipeline_steps.append("asr")
            logger.info(f"ASR complete: {len(raw_text)} chars")

        # Process text based on diarization results
        segments = []
        text = raw_text
        speaker_count_detected = 0

        if diarization_applied and speaker_segments:
            # NFA is required for accurate speaker attribution
            if nfa_applied and word_timestamps:
                # Use precise word-level merge
                logger.info("Using word-level merge (NFA)")
                segments = merge_words_with_speakers(word_timestamps, speaker_segments)
            else:
                # NFA failed - cannot do accurate speaker attribution
                # Skip diarization rather than provide inaccurate results
                logger.warning("NFA failed - skipping speaker attribution (would be inaccurate)")
                diarization_applied = False
                segments = []

            # Count unique speakers
            unique_speakers = set(seg.get("speaker") for seg in segments if seg.get("speaker"))
            speaker_count_detected = len(unique_speakers)

            # Apply punctuation and denormalization per segment
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
            logger.info(f"Merged text with {speaker_count_detected} speakers: {len(text)} chars")
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
