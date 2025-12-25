#!/usr/bin/env python3
"""
Compare multiple ASR pipeline implementations on the same audio file.

This script runs all 3 PROTOVERB ASR pipelines (nfa, mms, pyannote) sequentially
in Docker containers on the same audio file with identical parameters, saves
individual JSON results, and generates a comparison summary report.

Usage:
    # Run all pipelines with default settings
    python scripts/compare_pipelines.py audio.wav

    # Run with diarization enabled
    python scripts/compare_pipelines.py audio.wav --diarize

    # Run specific pipelines only
    python scripts/compare_pipelines.py audio.wav --pipelines nfa,pyannote

    # Custom output directory
    python scripts/compare_pipelines.py audio.wav --output-dir ./my_results

    # With WER calculation against reference transcript
    python scripts/compare_pipelines.py audio.wav --reference transcript.txt

Requirements:
    - Docker installed (images auto-built if missing)
    - HF_TOKEN for pyannote pipeline (via env var or .env file)
"""
import argparse
import json
import os
import subprocess
import sys
import time
import wave
from datetime import datetime
from pathlib import Path

# Add parent directories to path for imports
SCRIPT_DIR = Path(__file__).parent
SLOVENIAN_ASR_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = SLOVENIAN_ASR_DIR.parent

# Docker image naming convention
DOCKER_IMAGES = {
    "nfa": "slovene-asr-nfa",
    "mms": "slovene-asr-mms",
    "pyannote": "slovene-asr-pyannote"
}

# Pipeline directory names (for building)
PIPELINE_DIRS = {
    "nfa": "nemo-protoverb-nfa",
    "mms": "nemo-protoverb-mms",
    "pyannote": "nemo-protoverb-pyannote"
}

ALL_PIPELINES = list(DOCKER_IMAGES.keys())

# Pipelines requiring HuggingFace token for build
PIPELINES_REQUIRING_HF_TOKEN = {"pyannote"}


def load_env_file() -> dict:
    """Load environment variables from .env file if it exists."""
    env_vars = {}

    # Check multiple locations for .env file
    env_paths = [
        SCRIPT_DIR / ".env",           # scripts/.env
        SLOVENIAN_ASR_DIR / ".env",    # slovenian-asr/.env
    ]

    for env_path in env_paths:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, _, value = line.partition('=')
                        # Remove quotes if present
                        value = value.strip().strip('"').strip("'")
                        env_vars[key.strip()] = value
            break  # Use first .env found

    return env_vars


def get_hf_token() -> str | None:
    """Get HuggingFace token from environment or .env file."""
    # First check environment variable
    token = os.environ.get("HF_TOKEN")
    if token:
        return token

    # Fall back to .env file
    env_vars = load_env_file()
    return env_vars.get("HF_TOKEN")


def format_time(seconds: float) -> str:
    """Format seconds as human-readable string."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.1f}s"


def get_audio_info(audio_path: Path) -> dict:
    """Get basic info about audio file."""
    size_kb = audio_path.stat().st_size / 1024

    duration = None
    try:
        with wave.open(str(audio_path), 'rb') as w:
            frames = w.getnframes()
            rate = w.getframerate()
            duration = frames / float(rate)
    except Exception:
        pass

    return {
        "filename": audio_path.name,
        "size_kb": size_kb,
        "duration": duration
    }


def check_docker_available() -> bool:
    """Check if Docker is available."""
    try:
        result = subprocess.run(
            ["docker", "version"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_docker_image(image_name: str) -> bool:
    """Check if a Docker image exists locally."""
    result = subprocess.run(
        ["docker", "image", "inspect", image_name],
        capture_output=True
    )
    return result.returncode == 0


def build_docker_image(pipeline_name: str) -> bool:
    """Build a Docker image for a pipeline."""
    image = DOCKER_IMAGES[pipeline_name]
    pipeline_dir = SLOVENIAN_ASR_DIR / PIPELINE_DIRS[pipeline_name]

    if not pipeline_dir.exists():
        print(f"  Error: Pipeline directory not found: {pipeline_dir}")
        return False

    # Check if HF_TOKEN is required
    build_args = []
    if pipeline_name in PIPELINES_REQUIRING_HF_TOKEN:
        hf_token = get_hf_token()
        if not hf_token:
            print(f"  Error: {pipeline_name} requires HF_TOKEN for building.")
            print(f"  Set it via:")
            print(f"    export HF_TOKEN=hf_your_token_here")
            print(f"  Or create .env file in slovenian-asr/ or scripts/ with:")
            print(f"    HF_TOKEN=hf_your_token_here")
            print(f"  Get token from: https://huggingface.co/settings/tokens")
            return False
        build_args = ["--build-arg", f"HF_TOKEN={hf_token}"]
        print(f"  Using HF_TOKEN for pyannote model access")

    print(f"  Building {image} from {PIPELINE_DIRS[pipeline_name]}/...")
    print(f"  (This may take several minutes on first build)")

    try:
        cmd = ["docker", "build", "-t", image] + build_args + ["."]
        result = subprocess.run(
            cmd,
            cwd=pipeline_dir,
            timeout=1800,  # 30 minute timeout for build
            capture_output=False  # Show build output
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"  Error: Build timed out after 30 minutes")
        return False
    except Exception as e:
        print(f"  Error: Build failed: {e}")
        return False


def run_pipeline_in_docker(
    pipeline_name: str,
    audio_path: Path,
    params: dict,
    output_dir: Path,
    verbose: bool = False
) -> dict:
    """
    Run a pipeline inside its Docker container.

    Returns the handler result with timing information.
    """
    image = DOCKER_IMAGES[pipeline_name]

    # Format parameters for Python script
    punctuate = str(params.get("punctuate", True))
    denormalize = str(params.get("denormalize", True))
    diarize = str(params.get("enable_diarization", False))
    style = params.get("denormalize_style", "default")
    speakers = params.get("speaker_count")
    max_speakers = params.get("max_speakers", 10)

    # Handle None for speakers
    speakers_str = "None" if speakers is None else str(speakers)

    # Python script to run inside container
    # When verbose, writes result to mounted file instead of stdout
    python_script = f'''
import base64
import json
import sys
import time

sys.path.insert(0, '/app')
from handler import load_models_parallel, handler

# Load models
load_start = time.time()
load_models_parallel(
    need_asr=True,
    need_punct={punctuate},
    need_denorm={denormalize},
    need_diarization={diarize}
)
load_time = time.time() - load_start

# Read and encode audio
audio_b64 = base64.b64encode(open('/audio/input.wav', 'rb').read()).decode()

# Run handler
result = handler({{"input": {{
    "audio_base64": audio_b64,
    "punctuate": {punctuate},
    "denormalize": {denormalize},
    "denormalize_style": "{style}",
    "enable_diarization": {diarize},
    "speaker_count": {speakers_str},
    "max_speakers": {max_speakers}
}}}})

# Add timing metadata
result["_model_load_time"] = load_time
result["_pipeline"] = "{pipeline_name}"

# Write to file (for verbose mode) and stdout
with open('/output/result.json', 'w') as f:
    json.dump(result, f)
print(json.dumps(result))
'''

    # Build docker run command with output mount
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{audio_path.absolute()}:/audio/input.wav:ro",
        "-v", f"{output_dir.absolute()}:/output:rw",
        image, "python", "-c", python_script
    ]

    print(f"  Starting Docker container ({image})...")
    start_time = time.time()

    try:
        # When verbose, don't capture output - let it stream to terminal
        result = subprocess.run(
            cmd,
            capture_output=not verbose,
            text=True,
            timeout=600  # 10 minute timeout
        )
    except subprocess.TimeoutExpired:
        return {"error": "Container timed out after 10 minutes"}

    total_time = time.time() - start_time

    if result.returncode != 0:
        if verbose:
            return {"error": "Container failed (see output above)"}
        error_msg = result.stderr.strip() if result.stderr else "Unknown error"
        if len(error_msg) > 500:
            error_msg = error_msg[:500] + "..."
        return {"error": f"Container failed: {error_msg}"}

    # Parse JSON output - from file if verbose, from stdout otherwise
    try:
        # Try reading from mounted output file first (works for both modes)
        output_json_file = output_dir / "result.json"
        if output_json_file.exists():
            output = json.loads(output_json_file.read_text())
            output_json_file.unlink()  # Clean up temp file
        else:
            # Fall back to parsing stdout
            stdout = result.stdout.strip() if result.stdout else ""
            json_start = stdout.rfind('\n{')
            if json_start != -1:
                stdout = stdout[json_start + 1:]
            elif not stdout.startswith('{'):
                for line in stdout.split('\n'):
                    if line.strip().startswith('{'):
                        stdout = line.strip()
                        break
            output = json.loads(stdout)

        output["_total_time"] = total_time
        return output

    except json.JSONDecodeError as e:
        preview = result.stdout[:200] if result.stdout else "(empty)"
        return {"error": f"Failed to parse JSON output: {e}\nOutput preview: {preview}"}


def calculate_wer_for_result(result: dict, reference: str) -> dict | None:
    """Calculate WER for a pipeline result against reference transcript."""
    try:
        # Import WER calculation from project scripts
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from calculate_wer import calculate_wer
        sys.path.remove(str(PROJECT_ROOT / "scripts"))

        hypothesis = result.get("text", "")
        if not hypothesis:
            return None

        return calculate_wer(reference, hypothesis)
    except ImportError:
        print("  Warning: calculate_wer.py not found, skipping WER calculation")
        return None
    except Exception as e:
        print(f"  Warning: WER calculation failed: {e}")
        return None


def generate_summary_report(
    audio_info: dict,
    params: dict,
    results: dict[str, dict],
    wer_results: dict[str, dict] | None = None
) -> str:
    """Generate markdown summary report."""
    lines = [
        "# ASR Pipeline Comparison Report",
        "",
        f"**Audio:** {audio_info['filename']} ({audio_info['size_kb']:.0f}KB",
    ]

    if audio_info['duration']:
        lines[-1] += f", {audio_info['duration']:.1f}s)"
    else:
        lines[-1] += ")"

    lines.extend([
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Parameters",
        "```json",
        json.dumps(params, indent=2),
        "```",
        "",
        "## Processing Time",
        "",
        "| Pipeline | Model Load | Processing | Total |",
        "|----------|------------|------------|-------|",
    ])

    for pipeline_name, result in results.items():
        if "error" in result:
            lines.append(f"| {pipeline_name} | - | ERROR | - |")
        else:
            load_time = result.get("_model_load_time", 0)
            proc_time = result.get("processing_time", 0)
            total_time = result.get("_total_time", 0)
            lines.append(
                f"| {pipeline_name} | {format_time(load_time)} | "
                f"{format_time(proc_time)} | {format_time(total_time)} |"
            )

    lines.extend(["", "## Transcription Results", ""])

    for pipeline_name, result in results.items():
        lines.append(f"### {pipeline_name}")
        if "error" in result:
            lines.append(f"**ERROR:** {result['error']}")
        else:
            text = result.get("text", "(no text)")
            lines.append(f"> {text}")
        lines.append("")

    # Diarization section if enabled
    if params.get("enable_diarization", False):
        lines.extend(["## Diarization Results", ""])
        lines.append("| Pipeline | Speakers | Segments | Word-level |")
        lines.append("|----------|----------|----------|------------|")

        for pipeline_name, result in results.items():
            if "error" in result:
                lines.append(f"| {pipeline_name} | - | - | - |")
            elif result.get("diarization_applied"):
                speakers = result.get("speaker_count_detected", "?")
                segments = len(result.get("segments", []))
                word_level = "Yes" if result.get("word_level_timestamps") else "No"
                lines.append(f"| {pipeline_name} | {speakers} | {segments} | {word_level} |")
            else:
                lines.append(f"| {pipeline_name} | - | - | - |")

        lines.append("")

    # WER section if reference provided
    if wer_results:
        lines.extend(["## WER Analysis", ""])
        lines.append("| Pipeline | WER | Errors | Subs | Ins | Del |")
        lines.append("|----------|-----|--------|------|-----|-----|")

        for pipeline_name, wer in wer_results.items():
            if wer:
                lines.append(
                    f"| {pipeline_name} | {wer['wer']:.1f}% | {wer['total_errors']} | "
                    f"{wer['substitutions']} | {wer['insertions']} | {wer['deletions']} |"
                )
            else:
                lines.append(f"| {pipeline_name} | - | - | - | - | - |")

        lines.append("")

    # Raw text comparison
    lines.extend(["## Raw ASR Output (before punctuation/denormalization)", ""])

    for pipeline_name, result in results.items():
        lines.append(f"### {pipeline_name}")
        if "error" in result:
            lines.append("**ERROR**")
        else:
            raw_text = result.get("raw_text", "(no raw text)")
            lines.append(f"> {raw_text}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Compare ASR pipeline implementations on the same audio (via Docker)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/compare_pipelines.py audio.wav
  python scripts/compare_pipelines.py audio.wav --diarize
  python scripts/compare_pipelines.py audio.wav --pipelines nfa,pyannote
  python scripts/compare_pipelines.py audio.wav --reference transcript.txt

Docker images (auto-built if missing):
  - slovene-asr-nfa
  - slovene-asr-mms
  - slovene-asr-pyannote (requires HF_TOKEN)

HF_TOKEN for pyannote:
  export HF_TOKEN=hf_xxx  OR  create .env file with HF_TOKEN=hf_xxx
        """
    )

    parser.add_argument("audio", type=Path, help="Path to audio file (WAV, 16kHz mono)")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Output directory (default: ./comparison_results/<timestamp>_<audio>)")
    parser.add_argument("--pipelines", type=str, default=",".join(ALL_PIPELINES),
                        help=f"Comma-separated list of pipelines (default: {','.join(ALL_PIPELINES)})")
    parser.add_argument("--punctuate", action="store_true", default=True,
                        help="Add punctuation (default: true)")
    parser.add_argument("--no-punctuate", action="store_false", dest="punctuate",
                        help="Skip punctuation")
    parser.add_argument("--denormalize", action="store_true", default=True,
                        help="Apply denormalization (default: true)")
    parser.add_argument("--no-denormalize", action="store_false", dest="denormalize",
                        help="Skip denormalization")
    parser.add_argument("--style", choices=["default", "technical", "everyday"],
                        default="default", help="Denormalization style")
    parser.add_argument("--diarize", action="store_true",
                        help="Enable speaker diarization")
    parser.add_argument("--speakers", type=int, default=None,
                        help="Known number of speakers (default: auto-detect)")
    parser.add_argument("--max-speakers", type=int, default=10,
                        help="Maximum speakers for auto-detect (default: 10)")
    parser.add_argument("--reference", type=Path, default=None,
                        help="Reference transcript file for WER calculation")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show Docker container output in real-time")

    args = parser.parse_args()

    # Check Docker is available
    if not check_docker_available():
        print("Error: Docker is not available. Please install and start Docker.")
        sys.exit(1)

    # Validate audio file
    if not args.audio.exists():
        print(f"Error: Audio file not found: {args.audio}")
        sys.exit(1)

    # Parse pipeline list
    pipelines = [p.strip() for p in args.pipelines.split(",")]
    for p in pipelines:
        if p not in DOCKER_IMAGES:
            print(f"Error: Unknown pipeline '{p}'. Valid options: {', '.join(ALL_PIPELINES)}")
            sys.exit(1)

    # Check Docker images exist, build if missing
    for p in pipelines:
        image = DOCKER_IMAGES[p]
        if not check_docker_image(image):
            print(f"\nDocker image '{image}' not found. Building...")
            if not build_docker_image(p):
                print(f"Error: Failed to build {image}")
                sys.exit(1)
            print(f"Successfully built {image}\n")

    # Load reference transcript if provided
    reference_text = None
    if args.reference:
        if not args.reference.exists():
            print(f"Error: Reference file not found: {args.reference}")
            sys.exit(1)
        reference_text = args.reference.read_text(encoding="utf-8")

    # Create output directory
    audio_stem = args.audio.stem
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = SLOVENIAN_ASR_DIR / "comparison_results" / f"{timestamp}_{audio_stem}"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Get audio info
    audio_info = get_audio_info(args.audio)

    # Build pipeline parameters
    params = {
        "punctuate": args.punctuate,
        "denormalize": args.denormalize,
        "denormalize_style": args.style,
        "enable_diarization": args.diarize,
        "speaker_count": args.speakers,
        "max_speakers": args.max_speakers,
    }

    # Print header
    print()
    print("=" * 70)
    print(" ASR Pipeline Comparison (Docker)")
    print("=" * 70)
    duration_str = f", {audio_info['duration']:.1f}s" if audio_info['duration'] else ""
    print(f" Audio: {audio_info['filename']} ({audio_info['size_kb']:.0f}KB{duration_str})")
    print(f" Pipelines: {', '.join(pipelines)}")
    print(f" Output: {output_dir}")
    print("-" * 70)

    # Save input parameters
    input_params = {
        "audio_file": str(args.audio.absolute()),
        "audio_info": audio_info,
        "pipelines": pipelines,
        "docker_images": {p: DOCKER_IMAGES[p] for p in pipelines},
        "parameters": params,
        "reference_file": str(args.reference.absolute()) if args.reference else None,
        "timestamp": timestamp,
    }
    (output_dir / "input_params.json").write_text(
        json.dumps(input_params, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    # Run each pipeline
    results: dict[str, dict] = {}
    wer_results: dict[str, dict] = {} if reference_text else None

    for i, pipeline_name in enumerate(pipelines, 1):
        print()
        print(f"[{i}/{len(pipelines)}] Running {pipeline_name} pipeline...")
        print("-" * 40)

        result = run_pipeline_in_docker(pipeline_name, args.audio, params, output_dir, args.verbose)
        results[pipeline_name] = result

        # Save individual result
        result_file = output_dir / f"{pipeline_name}.json"
        result_file.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"  Result saved to {result_file.name}")

        # Calculate WER if reference provided
        if reference_text:
            wer = calculate_wer_for_result(result, reference_text)
            wer_results[pipeline_name] = wer
            if wer:
                print(f"  WER: {wer['wer']:.1f}%")

        # Print summary
        if "error" in result:
            print(f"  Status: ERROR - {result['error'][:100]}...")
        else:
            print(f"  Processing time: {format_time(result.get('processing_time', 0))}")
            print(f"  Total time (incl. container): {format_time(result.get('_total_time', 0))}")
            if result.get("diarization_applied"):
                print(f"  Speakers detected: {result.get('speaker_count_detected', '?')}")
                print(f"  Segments: {len(result.get('segments', []))}")

    # Generate summary report
    print()
    print("-" * 70)
    print(" Generating summary report...")

    summary = generate_summary_report(audio_info, params, results, wer_results)
    summary_file = output_dir / "summary.md"
    summary_file.write_text(summary, encoding="utf-8")
    print(f" Summary saved to {summary_file}")

    # Print final summary
    print()
    print("=" * 70)
    print(" Comparison Complete")
    print("=" * 70)
    print(f" Output directory: {output_dir}")
    print(" Files created:")
    for f in sorted(output_dir.iterdir()):
        print(f"   - {f.name}")
    print("=" * 70)


if __name__ == "__main__":
    main()
