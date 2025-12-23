#!/usr/bin/env python3
"""
Local test script for Slovenian ASR pipeline with speaker diarization.

This script imports and uses the same functions as handler.py,
allowing you to test the pipeline locally before deploying to RunPod.

Usage:
    # Full pipeline (ASR + Punctuation + Denormalization)
    python test_local.py test_audio.wav

    # ASR only
    python test_local.py test_audio.wav --asr-only

    # ASR + Punctuation (no denormalization)
    python test_local.py test_audio.wav --no-denormalize

    # ASR + Denormalization (no punctuation)
    python test_local.py test_audio.wav --no-punctuate

    # Different denormalization style
    python test_local.py test_audio.wav --style technical

    # With speaker diarization
    python test_local.py test_audio.wav --diarize

    # Diarization with known speaker count
    python test_local.py test_audio.wav --diarize --speakers 2

    # Compare all pipeline configurations
    python test_local.py test_audio.wav --compare

Requirements:
    - Models downloaded (run ./download_models.sh first)
    - NeMo toolkit installed
    - Slovene_denormalizator cloned
"""
import argparse
import base64
import os
import sys
import time
from pathlib import Path

# Ensure handler.py can be imported
sys.path.insert(0, str(Path(__file__).parent))

import handler as handler_module
from handler import (
    load_models_parallel,
    handler,
)


def format_time(seconds: float) -> str:
    """Format seconds as human-readable string."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    return f"{seconds:.1f}s"


def get_audio_info(audio_path: Path) -> dict:
    """Get basic info about audio file."""
    size_kb = audio_path.stat().st_size / 1024

    # Try to get duration using mutagen or wave
    duration = None
    try:
        import wave
        with wave.open(str(audio_path), 'rb') as w:
            frames = w.getnframes()
            rate = w.getframerate()
            duration = frames / float(rate)
    except Exception:
        pass

    return {
        "size_kb": size_kb,
        "duration": duration
    }


def run_pipeline(
    audio_path: Path,
    punctuate: bool,
    denormalize: bool,
    style: str,
    diarize: bool = False,
    speaker_count: int | None = None,
    max_speakers: int = 10
) -> dict:
    """Run the ASR pipeline with specified options."""
    # Read and encode audio
    audio_bytes = audio_path.read_bytes()
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    # Build job input (same format as RunPod)
    job = {
        "input": {
            "audio_base64": audio_base64,
            "filename": audio_path.name,
            "punctuate": punctuate,
            "denormalize": denormalize,
            "denormalize_style": style,
            "enable_diarization": diarize,
            "speaker_count": speaker_count,
            "max_speakers": max_speakers
        }
    }

    # Call the handler (same as RunPod would)
    return handler(job)


def print_header(audio_path: Path, audio_info: dict):
    """Print test header."""
    print()
    print("=" * 70)
    print(" Slovenian ASR Pipeline - Local Test")
    print("=" * 70)

    duration_str = f", {audio_info['duration']:.1f}s" if audio_info['duration'] else ""
    print(f" Audio: {audio_path.name} ({audio_info['size_kb']:.0f}KB{duration_str})")


def print_result(result: dict, punctuate: bool, denormalize: bool, style: str, diarize: bool = False, verbose: bool = False):
    """Print pipeline result."""
    opts = f"punctuate={punctuate}, denormalize={denormalize}, style={style}"
    if diarize:
        opts += f", diarize={diarize}"
    print(f" Options: {opts}")
    print("-" * 70)
    print()

    if "error" in result:
        print(f" ERROR: {result['error']}")
        return

    pipeline = result.get("pipeline", [])

    # Show each step
    step_num = 1

    if "asr" in pipeline:
        print(f" [{step_num}] ASR ({result.get('model_version', 'unknown')})")
        print(f"     -> \"{result.get('raw_text', '')}\"")
        print()
        step_num += 1

    if "align" in pipeline:
        print(f" [{step_num}] NFA Alignment (word-level timestamps)")
        print(f"     -> Word timestamps extracted for precise speaker assignment")
        print()
        step_num += 1

    if "diarize" in pipeline:
        speaker_count = result.get("speaker_count_detected", 0)
        segments = result.get("segments", [])
        word_level = result.get("word_level_timestamps", False)
        merge_method = "word-level (NFA)" if word_level else "proportional (fallback)"
        print(f" [{step_num}] Diarization ({speaker_count} speakers, {len(segments)} segments)")
        print(f"     Merge method: {merge_method}")

        # Show all segments in verbose mode, otherwise first 5
        segments_to_show = segments if verbose else segments[:5]
        for seg in segments_to_show:
            text = seg.get('text', '')
            text_display = f"{text[:50]}..." if len(text) > 50 and not verbose else text
            print(f"     {seg.get('speaker')}: [{seg.get('start', 0):.2f}s-{seg.get('end', 0):.2f}s] \"{text_display}\"")

            # Show word-level details in verbose mode if available
            if verbose and "words" in seg:
                for word_info in seg["words"][:10]:  # Limit to first 10 words
                    print(f"       • \"{word_info['word']}\" [{word_info['start']:.2f}s-{word_info['end']:.2f}s]")
                if len(seg.get("words", [])) > 10:
                    print(f"       ... and {len(seg['words']) - 10} more words")

        if not verbose and len(segments) > 5:
            print(f"     ... and {len(segments) - 5} more segments (use --verbose to see all)")
        print()
        step_num += 1

    if "punctuate" in pipeline:
        # Show intermediate if we also have denormalize
        if "denormalize" in pipeline:
            print(f" [{step_num}] Punctuation")
            print(f"     -> (applied)")
            print()
        else:
            print(f" [{step_num}] Punctuation")
            print(f"     -> \"{result.get('text', '')}\"")
            print()
        step_num += 1

    if "denormalize" in pipeline:
        print(f" [{step_num}] Denormalization (style={style})")
        print(f"     -> \"{result.get('text', '')}\"")
        print()

    # Final result
    print("-" * 70)
    print(f" Final: \"{result.get('text', '')}\"")
    print(f" Time:  {format_time(result.get('processing_time', 0))}")
    print(f" Steps: {' -> '.join(pipeline)}")
    if result.get("diarization_applied"):
        print(f" Speakers: {result.get('speaker_count_detected', 0)}")
        if result.get("word_level_timestamps"):
            print(f" Word timestamps: Yes (NFA)")
        else:
            print(f" Word timestamps: No (proportional fallback)")
    print("=" * 70)
    print()


def run_comparison(audio_path: Path, audio_info: dict, style: str):
    """Run and compare all pipeline configurations."""
    print_header(audio_path, audio_info)
    print(" Mode: COMPARISON (all configurations)")
    print("-" * 70)
    print()

    configs = [
        ("ASR only", False, False),
        ("ASR + Punctuation", True, False),
        ("ASR + Denormalization", False, True),
        ("Full pipeline", True, True),
    ]

    results = []

    for name, punctuate, denormalize in configs:
        print(f" Running: {name}...", end=" ", flush=True)
        start = time.time()
        result = run_pipeline(audio_path, punctuate, denormalize, style)
        elapsed = time.time() - start
        print(f"{format_time(elapsed)}")
        results.append((name, result, elapsed))

    print()
    print("-" * 70)
    print(" Results:")
    print("-" * 70)

    for name, result, elapsed in results:
        if "error" in result:
            print(f" {name}:")
            print(f"   ERROR: {result['error']}")
        else:
            print(f" {name} ({format_time(elapsed)}):")
            print(f"   \"{result.get('text', '')}\"")
        print()

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Test Slovenian ASR pipeline locally",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_local.py audio.wav                    # Full pipeline
  python test_local.py audio.wav --asr-only         # ASR only
  python test_local.py audio.wav --no-punctuate     # Skip punctuation
  python test_local.py audio.wav --no-denormalize   # Skip denormalization
  python test_local.py audio.wav --style technical  # Technical style
  python test_local.py audio.wav --diarize          # With speaker diarization
  python test_local.py audio.wav --diarize --speakers 2  # Known speaker count
  python test_local.py audio.wav --compare          # Compare all modes
        """
    )

    parser.add_argument("audio", type=Path, help="Path to audio file (WAV, 16kHz mono)")
    parser.add_argument("--asr-only", action="store_true",
                        help="Run ASR only (no punctuation or denormalization)")
    parser.add_argument("--no-punctuate", action="store_true",
                        help="Skip punctuation step")
    parser.add_argument("--no-denormalize", action="store_true",
                        help="Skip denormalization step")
    parser.add_argument("--style", choices=["default", "technical", "everyday"],
                        default="default", help="Denormalization style")
    parser.add_argument("--diarize", action="store_true",
                        help="Enable speaker diarization")
    parser.add_argument("--speakers", type=int, default=None,
                        help="Known number of speakers (1-10, default: auto-detect)")
    parser.add_argument("--max-speakers", type=int, default=10,
                        help="Maximum speakers for auto-detect (default: 10)")
    parser.add_argument("--compare", action="store_true",
                        help="Run and compare all pipeline configurations")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show all diarization segments and full text (not truncated)")

    args = parser.parse_args()

    # Validate audio file
    if not args.audio.exists():
        print(f"Error: Audio file not found: {args.audio}")
        sys.exit(1)

    # Get audio info
    audio_info = get_audio_info(args.audio)

    # Determine pipeline options
    if args.asr_only:
        punctuate = False
        denormalize = False
    else:
        punctuate = not args.no_punctuate
        denormalize = not args.no_denormalize

    diarize = args.diarize
    speaker_count = args.speakers
    max_speakers = args.max_speakers

    # Load only the models we need (in parallel)
    try:
        load_models_parallel(
            need_asr=True,
            need_punct=punctuate,
            need_denorm=denormalize,
            need_diarization=diarize
        )
    except Exception as e:
        print(f"  Model loading FAILED: {e}")
        sys.exit(1)

    # Report what's loaded
    if handler_module.ASR_MODEL:
        print("  ✓ ASR model ready")
    if handler_module.PUNCTUATOR_MODEL:
        print("  ✓ Punctuator ready")
    if handler_module.DENORMALIZER:
        print("  ✓ Denormalizer ready")
    if handler_module.VAD_MODEL and handler_module.SPEAKER_MODEL:
        print("  ✓ Diarization models ready")

    # Run test
    if args.compare:
        run_comparison(args.audio, audio_info, args.style)
    else:
        print_header(args.audio, audio_info)
        result = run_pipeline(
            args.audio, punctuate, denormalize, args.style,
            diarize=diarize, speaker_count=speaker_count, max_speakers=max_speakers
        )
        print_result(result, punctuate, denormalize, args.style, diarize=diarize, verbose=args.verbose)


if __name__ == "__main__":
    main()
