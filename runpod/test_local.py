#!/usr/bin/env python3
"""
Local test script for Slovenian ASR pipeline.

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


def run_pipeline(audio_path: Path, punctuate: bool, denormalize: bool, style: str) -> dict:
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
            "denormalize_style": style
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


def print_result(result: dict, punctuate: bool, denormalize: bool, style: str):
    """Print pipeline result."""
    print(f" Options: punctuate={punctuate}, denormalize={denormalize}, style={style}")
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
    parser.add_argument("--compare", action="store_true",
                        help="Run and compare all pipeline configurations")

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

    # Load only the models we need (in parallel)
    print()
    print("Loading models...")
    start = time.time()

    try:
        load_models_parallel(need_asr=True, need_punct=punctuate, need_denorm=denormalize)
        print(f"  Models loaded in {format_time(time.time() - start)}")
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

    # Run test
    if args.compare:
        run_comparison(args.audio, audio_info, args.style)
    else:
        print_header(args.audio, audio_info)
        result = run_pipeline(args.audio, punctuate, denormalize, args.style)
        print_result(result, punctuate, denormalize, args.style)


if __name__ == "__main__":
    main()
