"""
Re-run or re-evaluate a single cleanup configuration.

REASONING:
-----------
During parameter optimization testing, we may encounter anomalies (e.g., T3's
catastrophic duplication at temp=0.5) that warrant re-execution to verify
reproducibility. Additionally, we may want to re-score a result with fresh
evaluation criteria without burning API credits.

This script supports BOTH scenarios while preserving historical data:
1. Re-execute: Trigger fresh API call, save as new version (T3_v2.json)
2. Re-evaluate: Load existing cached result for re-scoring (no API call)

WHY VERSIONING (not deletion):
- Preserves historical attempts for comparison
- Allows investigation of non-deterministic behavior
- Maintains complete audit trail of all API calls
- No risk of losing Groq API results

USAGE:
------
# Re-execute T3 (fresh API call, creates T3_v2.json):
python rerun_one_config.py T3 --model llama-3.3-70b-versatile --prompt dream_v7

# Re-evaluate T3 using latest cached version (no API call):
python rerun_one_config.py T3 --model llama-3.3-70b-versatile --prompt dream_v7 --evaluate

# Re-evaluate specific version:
python rerun_one_config.py T3 --model llama-3.3-70b-versatile --prompt dream_v7 --evaluate --version 2

# List all versions of a config:
python rerun_one_config.py T3 --model llama-3.3-70b-versatile --prompt dream_v7 --list-versions

ARCHITECTURE:
-------------
- Uses backend API (run_cleanups_api.py approach) for DB persistence
- Results visible in frontend and via /entries/{id}/cleaned endpoint
- Cache format matches run_cleanups_api.py for consistency
- Auto-detects next version number (T3.json → T3_v2.json → T3_v3.json)

CACHE STRUCTURE:
----------------
cache/{transcription_id}/{prompt_name}/{model_name}/
  - T3.json (first run)
  - T3_v2.json (second run)
  - T3_v3.json (third run)

Example: cache/5beeaea1-967a-4569-9c84-eccad8797b95/dream_v7/llama-3.3-70b-versatile/

Latest version = highest version number or base file (T3.json) if no versions exist
"""
import asyncio
import json
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file from project root
load_dotenv(project_root / ".env")

# Configuration
TRANSCRIPTION_ID = "70cfb2c5-89c1-4486-a752-bd7cba980d3d"
API_BASE_URL = "http://localhost:8000/api/v1"
POLL_INTERVAL = 2  # seconds
MAX_POLL_TIME = 120  # seconds


def get_cache_dir(prompt_name: str, model_name: str) -> Path:
    """
    Get cache directory for a specific transcription, prompt, and model.

    Format: cache/{transcription_id}/{prompt_name}/{sanitized_model_name}/
    Example: cache/5beeaea1-967a-4569-9c84-eccad8797b95/dream_v7/llama-3.3-70b-versatile/
    """
    # Sanitize model name for directory (replace / and : with -)
    safe_model_name = model_name.replace("/", "-").replace(":", "-")
    cache_dir = Path(__file__).parent / "cache" / TRANSCRIPTION_ID / prompt_name / safe_model_name
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

# Test configurations (same as run_cleanups_api.py)
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
    {"name": "B1", "temperature": 0.0, "top_p": 0.3},  # Best from T1 + Best from P2
]

ALL_CONFIGS = TEMP_CONFIGS + TOPP_CONFIGS + BOTH_CONFIGS


def find_config(config_name: str) -> Optional[Dict[str, Any]]:
    """Find config by name across all config lists."""
    for config in ALL_CONFIGS:
        if config["name"] == config_name:
            return config
    return None


def get_cache_filename(config_name: str, version: Optional[int] = None) -> str:
    """
    Get cache filename for a config and version.

    Examples:
        get_cache_filename("T3", None) -> "T3.json"
        get_cache_filename("T3", 2) -> "T3_v2.json"
    """
    if version is None or version == 1:
        return f"{config_name}.json"
    return f"{config_name}_v{version}.json"


def find_all_versions(config_name: str, cache_dir: Path) -> List[int]:
    """
    Find all existing versions of a config.

    Returns:
        List of version numbers (1 for base file, 2+ for versioned files)
    """
    versions = []

    # Check base file (version 1)
    base_file = cache_dir / f"{config_name}.json"
    if base_file.exists():
        versions.append(1)

    # Check versioned files (v2, v3, ...)
    version_num = 2
    while True:
        version_file = cache_dir / f"{config_name}_v{version_num}.json"
        if version_file.exists():
            versions.append(version_num)
            version_num += 1
        else:
            break

    return sorted(versions)


def get_next_version(config_name: str, cache_dir: Path) -> int:
    """Get next available version number for a config."""
    versions = find_all_versions(config_name, cache_dir)
    if not versions:
        return 1
    return max(versions) + 1


def load_cached_result(config_name: str, cache_dir: Path, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Load cached result for a config.

    Args:
        config_name: Config name (e.g., "T3")
        cache_dir: Cache directory path
        version: Specific version to load, or None for latest

    Returns:
        Cached result dict or None if not found
    """
    if version is None:
        # Load latest version
        versions = find_all_versions(config_name, cache_dir)
        if not versions:
            return None
        version = max(versions)

    filename = get_cache_filename(config_name, version)
    cache_file = cache_dir / filename

    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_to_cache(config_name: str, result: Dict[str, Any], version: int, cache_dir: Path) -> Path:
    """
    Save result to cache with version number.

    Returns:
        Path to saved cache file
    """
    filename = get_cache_filename(config_name, version)
    cache_file = cache_dir / filename

    # Add version metadata to result
    result["cache_version"] = version
    result["cache_filename"] = filename

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return cache_file


async def authenticate(client: httpx.AsyncClient, email: str, password: str) -> str:
    """
    Authenticate and get JWT access token.

    Returns:
        Access token string
    """
    response = await client.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    response.raise_for_status()
    data = response.json()
    return data["access_token"]


async def trigger_cleanup_via_api(
    client: httpx.AsyncClient,
    transcription_id: str,
    config: Dict[str, Any],
    model_name: str,
    token: str
) -> str:
    """
    Trigger cleanup via API endpoint.

    Returns:
        cleanup_id (UUID string)
    """
    config_name = config["name"]
    temperature = config["temperature"]
    top_p = config["top_p"]

    print(f"🚀 Triggering {config_name} via API (model={model_name}, temp={temperature}, top_p={top_p})...")

    # Build request body
    request_body = {"llm_model": model_name}
    if temperature is not None:
        request_body["temperature"] = temperature
    if top_p is not None:
        request_body["top_p"] = top_p

    try:
        response = await client.post(
            f"{API_BASE_URL}/transcriptions/{transcription_id}/cleanup",
            json=request_body,
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        data = response.json()
        cleanup_id = data["id"]

        print(f"   ✅ Cleanup triggered! ID: {cleanup_id}")
        return cleanup_id

    except httpx.HTTPStatusError as e:
        print(f"   ❌ API Error: {e.response.status_code} - {e.response.text}")
        raise


async def poll_cleanup_status(
    client: httpx.AsyncClient,
    cleanup_id: str,
    token: str,
    config_name: str
) -> Dict[str, Any]:
    """
    Poll cleanup status until completed or failed.

    Returns:
        Complete cleanup result
    """
    start_time = time.time()
    poll_count = 0

    while True:
        poll_count += 1
        elapsed = time.time() - start_time

        if elapsed > MAX_POLL_TIME:
            raise TimeoutError(f"Polling timeout after {MAX_POLL_TIME}s")

        try:
            response = await client.get(
                f"{API_BASE_URL}/cleaned-entries/{cleanup_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            data = response.json()

            status = data["status"]

            if status == "completed":
                processing_time = data.get("processing_time_seconds", 0)
                cleaned_length = len(data.get("cleaned_text", ""))
                print(f"   ✅ Completed! ({processing_time:.2f}s, {cleaned_length} chars)")
                return data

            elif status == "failed":
                error = data.get("error_message", "Unknown error")
                print(f"   ❌ Failed: {error}")
                return data

            elif status == "processing":
                print(f"   ⏳ Processing... (poll #{poll_count}, {elapsed:.1f}s elapsed)")
                await asyncio.sleep(POLL_INTERVAL)

            else:  # pending
                print(f"   ⏳ Pending... (poll #{poll_count}, {elapsed:.1f}s elapsed)")
                await asyncio.sleep(POLL_INTERVAL)

        except httpx.HTTPStatusError as e:
            print(f"   ❌ Polling error: {e.response.status_code} - {e.response.text}")
            raise


async def execute_cleanup(
    config_name: str,
    config: Dict[str, Any],
    model_name: str,
    client: httpx.AsyncClient,
    token: str,
    raw_length: int
) -> Dict[str, Any]:
    """
    Execute cleanup via API and return result.

    Returns:
        Result dict in cache format.
        Always includes cleanup_id and raw_response when available (even for failures).
    """
    temperature = config["temperature"]
    top_p = config["top_p"]
    cleanup_id = None
    raw_response = None

    try:
        # Trigger cleanup
        cleanup_id = await trigger_cleanup_via_api(client, TRANSCRIPTION_ID, config, model_name, token)

        # Poll for completion
        result = await poll_cleanup_status(client, cleanup_id, token, config_name)

        # Capture raw response (available for both success and failure)
        raw_response = result.get("llm_raw_response", "")

        # Safely extract analysis fields (handle None values)
        analysis = result.get("analysis") or {}

        # Calculate length metrics
        cleaned_text = result.get("cleaned_text", "")
        cleaned_length = len(cleaned_text)
        cleaned_raw_ratio = round(cleaned_length / raw_length, 4) if raw_length > 0 else 0

        # Transform API response to cache format
        cached_result = {
            "config": config_name,
            "cleanup_id": cleanup_id,
            "model": result.get("model_name", ""),
            "temperature": temperature,
            "top_p": top_p,
            "timestamp": result.get("created_at", datetime.now(timezone.utc).isoformat()),
            "processing_time_seconds": result.get("processing_time_seconds", 0),
            "prompt_id": result.get("prompt_template_id"),
            "prompt_name": result.get("prompt_name"),
            "transcription_id": TRANSCRIPTION_ID,
            "raw_length": raw_length,
            "cleaned_length": cleaned_length,
            "cleaned_raw_ratio": cleaned_raw_ratio,
            "cleaned_text": cleaned_text,
            "themes": analysis.get("themes", []),
            "emotions": analysis.get("emotions", []),
            "characters": analysis.get("characters", []),
            "locations": analysis.get("locations", []),
            "raw_response": raw_response,
            "status": "success" if result["status"] == "completed" else "failed",
            "error": result.get("error_message")
        }

        return cached_result

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return {
            "config": config_name,
            "cleanup_id": cleanup_id,  # Will be None if trigger failed, otherwise contains the ID
            "temperature": temperature,
            "top_p": top_p,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "transcription_id": TRANSCRIPTION_ID,
            "raw_length": raw_length,
            "cleaned_length": 0,
            "cleaned_raw_ratio": 0,
            "raw_response": raw_response,  # Will be None if polling failed before getting response
            "status": "failed",
            "error": str(e)
        }


def print_result_for_evaluation(config_name: str, result: Dict[str, Any], version: int, prompt_name: str):
    """Print result in format ready for manual scoring."""
    print(f"\n{'='*80}")
    print(f"RESULT FOR EVALUATION: {config_name} (version {version})")
    print(f"{'='*80}")

    print(f"\n📋 METADATA:")
    print(f"   Config: {config_name}")
    print(f"   Temperature: {result.get('temperature')}")
    print(f"   Top-p: {result.get('top_p')}")
    print(f"   Model: {result.get('model', 'N/A')}")
    print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
    print(f"   Processing time: {result.get('processing_time_seconds', 0):.2f}s")
    print(f"   Cache version: {version}")
    print(f"   Status: {result.get('status', 'unknown')}")

    if result.get('error'):
        print(f"   ❌ Error: {result['error']}")
        return

    cleaned_text = result.get('cleaned_text', '')
    print(f"   Length: {len(cleaned_text)} chars")

    print(f"\n📝 CLEANED TEXT:")
    print(f"{'-'*80}")
    print(cleaned_text)
    print(f"{'-'*80}")

    print(f"\n🔍 ANALYSIS:")
    print(f"   Themes: {result.get('themes', [])}")
    print(f"   Emotions: {result.get('emotions', [])}")
    print(f"   Characters: {result.get('characters', [])}")
    print(f"   Locations: {result.get('locations', [])}")

    # Load raw transcription for comparison
    data_file = Path(__file__).parent / "cache" / TRANSCRIPTION_ID / prompt_name / "fetched_data.json"
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            raw_text = data["transcription"]["text"]
            print(f"\n📄 RAW TRANSCRIPTION (for comparison):")
            print(f"   Length: {len(raw_text)} chars")
            print(f"   Ratio: {len(cleaned_text) / len(raw_text) * 100:.1f}%")
            print(f"{'-'*80}")
            print(raw_text)
            print(f"{'-'*80}")

    print(f"\n✅ Ready for manual scoring using CLAUDE_CODE_INSTRUCTIONS.md criteria")
    print(f"{'='*80}\n")


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Re-run or re-evaluate a single cleanup configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Re-execute T3 (fresh API call, creates new version):
  python rerun_one_config.py T3 --model llama-3.3-70b-versatile --prompt dream_v7

  # Re-evaluate T3 using latest cached version (no API call):
  python rerun_one_config.py T3 --model llama-3.3-70b-versatile --prompt dream_v7 --evaluate

  # Re-evaluate specific version:
  python rerun_one_config.py T3 --model llama-3.3-70b-versatile --prompt dream_v7 --evaluate --version 2

  # List all versions:
  python rerun_one_config.py T3 --model llama-3.3-70b-versatile --prompt dream_v7 --list-versions
        """
    )
    parser.add_argument("config_name", help="Config name (e.g., T3, P2, B1)")
    parser.add_argument(
        "model",
        type=str,
        help="LLM model name (required). Examples: llama-3.3-70b-versatile, openai/gpt-oss-120b"
    )
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        required=True,
        help="Prompt version name (required). Examples: dream_v5, dream_v7"
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Evaluate only (no API call, use cached result)"
    )
    parser.add_argument(
        "--version",
        type=int,
        help="Specific version to evaluate (default: latest)"
    )
    parser.add_argument(
        "--list-versions",
        action="store_true",
        help="List all existing versions and exit"
    )

    args = parser.parse_args()
    config_name = args.config_name.upper()
    model_name = args.model
    prompt_name = args.prompt

    # Get cache directory for this prompt and model
    cache_dir = get_cache_dir(prompt_name, model_name)

    print("="*80)
    print("Re-run One Config - Parameter Optimization Testing")
    print("="*80)
    print(f"Model: {model_name}")
    print(f"Prompt: {prompt_name}")
    print(f"Cache directory: {cache_dir}")

    # Find config
    config = find_config(config_name)
    if not config:
        print(f"❌ Error: Config '{config_name}' not found!")
        print(f"   Available configs: {', '.join([c['name'] for c in ALL_CONFIGS])}")
        return

    # List versions mode
    if args.list_versions:
        versions = find_all_versions(config_name, cache_dir)
        if not versions:
            print(f"\n📋 No versions found for {config_name}")
        else:
            print(f"\n📋 Versions found for {config_name}:")
            for v in versions:
                filename = get_cache_filename(config_name, v)
                result = load_cached_result(config_name, cache_dir, v)
                timestamp = result.get('timestamp', 'unknown') if result else 'unknown'
                status = result.get('status', 'unknown') if result else 'unknown'
                print(f"   v{v}: {filename} (timestamp: {timestamp}, status: {status})")
        return

    # Evaluate mode
    if args.evaluate:
        print(f"\n🔍 EVALUATE MODE: Loading cached result for {config_name}")
        print(f"   Temperature: {config.get('temperature')}")
        print(f"   Top-p: {config.get('top_p')}")

        result = load_cached_result(config_name, cache_dir, args.version)
        if not result:
            if args.version:
                print(f"\n❌ Error: No cached result found for {config_name} version {args.version}")
            else:
                print(f"\n❌ Error: No cached result found for {config_name}")
            print(f"   Run without --evaluate to execute fresh API call")
            return

        version = args.version if args.version else max(find_all_versions(config_name, cache_dir))
        print(f"   ✅ Loaded version {version}")
        print_result_for_evaluation(config_name, result, version, prompt_name)
        return

    # Execute mode
    print(f"\n🚀 EXECUTE MODE: Running fresh API call for {config_name}")
    print(f"   Temperature: {config.get('temperature')}")
    print(f"   Top-p: {config.get('top_p')}")

    next_version = get_next_version(config_name, cache_dir)
    print(f"   Will save as version {next_version}")

    # Load fetched data to get raw transcription length
    data_file = Path(__file__).parent / "cache" / TRANSCRIPTION_ID / prompt_name / "fetched_data.json"
    if not data_file.exists():
        print(f"\n❌ Error: {data_file} not found. Run fetch_data.py first!")
        return

    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    raw_length = len(data["transcription"]["text"])
    print(f"   Raw transcription length: {raw_length} chars")

    # Load credentials
    email = os.getenv("TEST_USER_EMAIL")
    password = os.getenv("TEST_USER_PASSWORD")

    if not email or not password:
        print("\n❌ Error: TEST_USER_EMAIL and TEST_USER_PASSWORD must be set in .env")
        print("   Add these lines to your .env file:")
        print("   TEST_USER_EMAIL=your-email@example.com")
        print("   TEST_USER_PASSWORD=your-password")
        return

    print(f"\n🌐 API Base URL: {API_BASE_URL}")
    print(f"👤 User: {email}")

    # Execute cleanup via API
    async with httpx.AsyncClient(timeout=180.0) as client:
        # Authenticate
        print(f"\n🔐 Authenticating...")
        try:
            token = await authenticate(client, email, password)
            print(f"   ✅ Authentication successful!")
        except Exception as e:
            print(f"   ❌ Authentication failed: {e}")
            return

        # Execute cleanup
        result = await execute_cleanup(config_name, config, model_name, client, token, raw_length)

        # Save to cache with version
        cache_file = save_to_cache(config_name, result, next_version, cache_dir)
        print(f"\n💾 Saved to cache: {cache_file.name}")
        print(f"   💽 Also saved to database (cleanup_id: {result.get('cleanup_id', 'N/A')})")

        # Print for evaluation
        print_result_for_evaluation(config_name, result, next_version, prompt_name)

        print(f"\n🌐 View in frontend or via API:")
        print(f"   GET {API_BASE_URL}/entries/{TRANSCRIPTION_ID}/cleaned")


if __name__ == "__main__":
    asyncio.run(main())