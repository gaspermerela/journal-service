"""
Execute dream cleanup tests with Groq API and cache results.

Usage:
    python run_cleanups.py --prompt <prompt_name>

Examples:
    python run_cleanups.py --prompt dream_v7
    python run_cleanups.py --prompt dream_v5

Cache Structure:
    cache/{transcription_id}/{prompt_name}/{model_name}/
    Example: cache/5beeaea1-967a-4569-9c84-eccad8797b95/dream_v7/llama-3.3-70b-versatile/
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file from project root
load_dotenv(project_root / ".env")

from groq import Groq

# Configuration
TRANSCRIPTION_ID = "5beeaea1-967a-4569-9c84-eccad8797b95"
GROQ_MODEL = "llama-3.3-70b-versatile"


def get_cache_dir(prompt_name: str) -> Path:
    """
    Get cache directory for a specific transcription, prompt, and model.

    Format: cache/{transcription_id}/{prompt_name}/{sanitized_model_name}/
    Example: cache/5beeaea1-967a-4569-9c84-eccad8797b95/dream_v7/llama-3.3-70b-versatile/
    """
    safe_model_name = GROQ_MODEL.replace("/", "-").replace(":", "-")
    cache_dir = Path(__file__).parent / "cache" / TRANSCRIPTION_ID / prompt_name / safe_model_name
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

# Test configurations
TEMP_CONFIGS = [
    {"name": "T1", "temperature": 0.0, "top_p": None},
    {"name": "T2", "temperature": 0.3, "top_p": None},
    {"name": "T3", "temperature": 0.5, "top_p": None},
    {"name": "T4", "temperature": 0.8, "top_p": None},
    {"name": "T5", "temperature": 1.0, "top_p": None},
    {"name": "T6", "temperature": 1.5, "top_p": None},
    {"name": "T7", "temperature": 2.0, "top_p": None},
]

TOPP_CONFIGS = [
    {"name": "P1", "temperature": None, "top_p": 0.1},
    {"name": "P2", "temperature": None, "top_p": 0.3},
    {"name": "P3", "temperature": None, "top_p": 0.5},
    {"name": "P4", "temperature": None, "top_p": 0.7},
    {"name": "P5", "temperature": None, "top_p": 0.9},
    {"name": "P6", "temperature": None, "top_p": 1.0},
]

BOTH_CONFIGS = [
    {"name": "B1", "temperature": 0.3, "top_p": 0.9},
    {"name": "B2", "temperature": 0.5, "top_p": 0.5},
    {"name": "B3", "temperature": 0.5, "top_p": 0.9},
    {"name": "B4", "temperature": 0.8, "top_p": 0.5},
]


def load_cached_result(config_name: str, cache_dir: Path) -> Optional[Dict[str, Any]]:
    """Load cached result if it exists."""
    cache_file = cache_dir / f"{config_name}.json"
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_to_cache(config_name: str, result: Dict[str, Any], cache_dir: Path) -> None:
    """Save result to cache."""
    cache_file = cache_dir / f"{config_name}.json"
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"   💾 Cached to: {cache_file.name}")


def run_cleanup(
    transcription: str,
    prompt_text: str,
    prompt_id: int,
    config: Dict[str, Any],
    groq_client: Groq
) -> Dict[str, Any]:
    """
    Execute a single cleanup with Groq API.

    Returns dict with cleaned_text, raw_response, and metadata.
    """
    config_name = config["name"]
    temperature = config["temperature"]
    top_p = config["top_p"]

    print(f"\n🚀 Executing {config_name} (temp={temperature}, top_p={top_p})...")

    # Prepare the full prompt
    # Replace {transcription_text} placeholder
    full_prompt = prompt_text.replace("{transcription_text}", transcription)

    # Replace {output_format} placeholder with JSON schema instruction
    # (Based on app/config.py OUTPUT_SCHEMAS for "dream" entry_type)
    json_schema = """Return your response as JSON with this exact structure:

{
  "cleaned_text": "...",
  "themes": ["...", "..."],
  "emotions": ["...", "..."],
  "characters": ["...", "..."],
  "locations": ["...", "..."]
}"""
    full_prompt = full_prompt.replace("{output_format}", json_schema)

    # Build API request parameters
    api_params = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": full_prompt}],
        "response_format": {"type": "json_object"},
    }

    # Add temperature or top_p (not both, per Groq recommendation)
    if temperature is not None:
        api_params["temperature"] = temperature
    if top_p is not None:
        api_params["top_p"] = top_p

    try:
        # Call Groq API
        start_time = datetime.now(timezone.utc)
        response = groq_client.chat.completions.create(**api_params)
        end_time = datetime.now(timezone.utc)

        # Extract response
        raw_response = response.choices[0].message.content
        processing_time = (end_time - start_time).total_seconds()

        # Parse JSON
        parsed = json.loads(raw_response)
        cleaned_text = parsed.get("cleaned_text", "")

        # Calculate length metrics
        raw_length = len(transcription)
        cleaned_length = len(cleaned_text)
        cleaned_raw_ratio = round(cleaned_length / raw_length, 4) if raw_length > 0 else 0

        print(f"   ✅ Success! ({processing_time:.2f}s, {cleaned_length} chars, {cleaned_raw_ratio*100:.1f}%)")

        return {
            "config": config_name,
            "model": GROQ_MODEL,
            "temperature": temperature,
            "top_p": top_p,
            "timestamp": start_time.isoformat(),
            "processing_time_seconds": processing_time,
            "prompt_id": prompt_id,
            "transcription_id": TRANSCRIPTION_ID,
            "raw_length": raw_length,
            "cleaned_length": cleaned_length,
            "cleaned_raw_ratio": cleaned_raw_ratio,
            "cleaned_text": cleaned_text,
            "themes": parsed.get("themes", []),
            "emotions": parsed.get("emotions", []),
            "characters": parsed.get("characters", []),
            "locations": parsed.get("locations", []),
            "raw_response": raw_response,
            "status": "success"
        }

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return {
            "config": config_name,
            "model": GROQ_MODEL,
            "temperature": temperature,
            "top_p": top_p,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt_id": prompt_id,
            "transcription_id": TRANSCRIPTION_ID,
            "raw_length": len(transcription),
            "cleaned_length": 0,
            "cleaned_raw_ratio": 0,
            "status": "failed",
            "error": str(e)
        }


def run_test_case(
    case_name: str,
    configs: list,
    transcription: str,
    prompt_text: str,
    prompt_id: int,
    groq_client: Groq,
    cache_dir: Path
) -> Dict[str, Dict[str, Any]]:
    """
    Run all configs for a test case, using cache when available.

    Returns: dict mapping config_name -> result
    """
    print(f"\n{'='*60}")
    print(f"  {case_name}")
    print(f"{'='*60}")

    results = {}

    for config in configs:
        config_name = config["name"]

        # Check cache first
        cached = load_cached_result(config_name, cache_dir)
        if cached:
            print(f"\n📦 {config_name} - Using cached result from {cached.get('timestamp', 'unknown')}")
            results[config_name] = cached
            continue

        # Execute cleanup
        result = run_cleanup(transcription, prompt_text, prompt_id, config, groq_client)

        # Cache immediately
        save_to_cache(config_name, result, cache_dir)

        results[config_name] = result

    return results


def main(prompt_name: str):
    """Main execution function."""
    print("Dream Cleanup Testing - Concurrent Batch Execution with Caching")
    print("="*60)

    # Get cache directory for this prompt
    cache_dir = get_cache_dir(prompt_name)

    # Load fetched data from transcription directory
    data_file = Path(__file__).parent / "cache" / TRANSCRIPTION_ID / "fetched_data.json"
    if not data_file.exists():
        print(f"❌ Error: {data_file} not found. Run fetch_data.py first!")
        return

    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    transcription_text = data["transcription"]["text"]
    prompt_text = data["prompt"]["text"]
    prompt_id = data["prompt"]["id"]

    print(f"📄 Transcription: {TRANSCRIPTION_ID}")
    print(f"📝 Prompt: {data['prompt']['name']} (v{data['prompt']['version']})")
    print(f"🤖 Model: {GROQ_MODEL}")
    print(f"📁 Cache directory: {cache_dir}")

    # Initialize Groq client
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("❌ Error: GROQ_API_KEY environment variable not set!")
        return

    groq_client = Groq(api_key=groq_api_key)

    # Run test cases
    all_results = {}

    # Case 1: Temperature only
    case1_results = run_test_case(
        "CASE 1: Temperature Only (top_p = null)",
        TEMP_CONFIGS,
        transcription_text,
        prompt_text,
        prompt_id,
        groq_client,
        cache_dir
    )
    all_results.update(case1_results)

    # Optionally run Case 2 and Case 3 (uncomment when ready)
    # case2_results = run_test_case(
    #     "CASE 2: Top-p Only (temperature = null)",
    #     TOPP_CONFIGS,
    #     transcription_text,
    #     prompt_text,
    #     prompt_id,
    #     groq_client,
    #     cache_dir
    # )
    # all_results.update(case2_results)

    # Save summary
    summary_file = cache_dir / "_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "transcription_id": TRANSCRIPTION_ID,
            "model": GROQ_MODEL,
            "prompt_id": prompt_id,
            "prompt_name": data['prompt']['name'],
            "prompt_version": data['prompt']['version'],
            "execution_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_configs_executed": len(all_results),
            "configs": list(all_results.keys())
        }, f, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ Execution complete!")
    print(f"   Total configs processed: {len(all_results)}")
    print(f"   Summary saved to: {summary_file}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Execute dream cleanup tests with Groq API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_cleanups.py --prompt dream_v7
    python run_cleanups.py --prompt dream_v5
        """
    )
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        required=True,
        help="Prompt version name (required). Examples: dream_v5, dream_v7"
    )

    args = parser.parse_args()
    main(args.prompt)