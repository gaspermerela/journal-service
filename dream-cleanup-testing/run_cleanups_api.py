"""
Execute dream cleanup tests via journal-service API and cache results.

This version uses the existing API endpoints instead of calling Groq directly,
which means results are automatically saved to the database and visible in the frontend.

Usage:
    python run_cleanups_api.py <model> [--case <1|2|3|all>]

Examples:
    python run_cleanups_api.py llama-3.3-70b-versatile --case 1   # Temperature only
    python run_cleanups_api.py gpt-oss-120b --case 2              # Top-p only
    python run_cleanups_api.py gpt-oss-120b --case all            # All cases

Cache Structure:
    cache/{transcription_id}_{model_name}/
    Example: cache/5beeaea1-967a-4569-9c84-eccad8797b95_llama-3.3-70b-versatile/
"""
import asyncio
import json
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv
import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file from project root
load_dotenv(project_root / ".env")

# Configuration
TRANSCRIPTION_ID = "5beeaea1-967a-4569-9c84-eccad8797b95"
API_BASE_URL = "http://localhost:8000/api/v1"
POLL_INTERVAL = 2  # seconds
MAX_POLL_TIME = 180  # seconds (increased for larger models)

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


def get_cache_dir(model_name: str) -> Path:
    """
    Get model-specific cache directory.

    Format: cache/{transcription_id}_{sanitized_model_name}/
    Example: cache/5beeaea1-967a-4569-9c84-eccad8797b95_llama-3.3-70b-versatile/
    """
    base_dir = Path(__file__).parent / "cache"
    # Sanitize model name for directory (replace / and : with -)
    safe_model_name = model_name.replace("/", "-").replace(":", "-")
    cache_dir = base_dir / f"{TRANSCRIPTION_ID}_{safe_model_name}"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def load_cached_result(cache_dir: Path, config_name: str) -> Optional[Dict[str, Any]]:
    """Load cached result if it exists."""
    cache_file = cache_dir / f"{config_name}.json"
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_to_cache(cache_dir: Path, config_name: str, result: Dict[str, Any]) -> None:
    """Save result to cache."""
    cache_file = cache_dir / f"{config_name}.json"
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"   Cached to: {cache_file.name}")


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
    token: str,
    model_name: str
) -> str:
    """
    Trigger cleanup via API endpoint.

    Returns:
        cleanup_id (UUID string)
    """
    config_name = config["name"]
    temperature = config["temperature"]
    top_p = config["top_p"]

    print(f"\n[TRIGGER] {config_name} (model={model_name}, temp={temperature}, top_p={top_p})...")

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

        print(f"   [OK] Cleanup triggered! ID: {cleanup_id}")
        return cleanup_id

    except httpx.HTTPStatusError as e:
        print(f"   [ERROR] API Error: {e.response.status_code} - {e.response.text}")
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
                print(f"   [DONE] Completed! ({processing_time:.2f}s, {cleaned_length} chars)")
                return data

            elif status == "failed":
                error = data.get("error_message", "Unknown error")
                print(f"   [FAIL] Failed: {error}")
                return data

            elif status == "processing":
                print(f"   [WAIT] Processing... (poll #{poll_count}, {elapsed:.1f}s elapsed)")
                await asyncio.sleep(POLL_INTERVAL)

            else:  # pending
                print(f"   [WAIT] Pending... (poll #{poll_count}, {elapsed:.1f}s elapsed)")
                await asyncio.sleep(POLL_INTERVAL)

        except httpx.HTTPStatusError as e:
            print(f"   [ERROR] Polling error: {e.response.status_code} - {e.response.text}")
            raise


async def run_cleanup_via_api(
    client: httpx.AsyncClient,
    transcription_id: str,
    config: Dict[str, Any],
    token: str,
    model_name: str
) -> Dict[str, Any]:
    """
    Execute a single cleanup via API and wait for completion.

    Returns dict with cleaned_text, analysis, and metadata.
    """
    config_name = config["name"]
    temperature = config["temperature"]
    top_p = config["top_p"]

    try:
        # Trigger cleanup
        cleanup_id = await trigger_cleanup_via_api(
            client, transcription_id, config, token, model_name
        )

        # Poll for completion
        result = await poll_cleanup_status(client, cleanup_id, token, config_name)

        # Transform API response to match our cache format
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
            "transcription_id": transcription_id,
            "cleaned_text": result.get("cleaned_text", ""),
            "themes": result.get("analysis", {}).get("themes", []),
            "emotions": result.get("analysis", {}).get("emotions", []),
            "characters": result.get("analysis", {}).get("characters", []),
            "locations": result.get("analysis", {}).get("locations", []),
            "raw_response": result.get("llm_raw_response", ""),
            "status": "success" if result["status"] == "completed" else "failed",
            "error": result.get("error_message")
        }

        return cached_result

    except Exception as e:
        print(f"   [ERROR] Error: {str(e)}")
        return {
            "config": config_name,
            "model": model_name,
            "temperature": temperature,
            "top_p": top_p,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "transcription_id": transcription_id,
            "status": "failed",
            "error": str(e)
        }


async def run_test_case(
    case_name: str,
    configs: list,
    transcription_id: str,
    client: httpx.AsyncClient,
    token: str,
    cache_dir: Path,
    model_name: str
) -> Dict[str, Dict[str, Any]]:
    """
    Run all configs for a test case, using cache when available.

    Returns: dict mapping config_name -> result
    """
    print(f"\n{'='*60}")
    print(f"  {case_name}")
    print(f"  Model: {model_name}")
    print(f"{'='*60}")

    results = {}

    for config in configs:
        config_name = config["name"]

        # Check cache first
        cached = load_cached_result(cache_dir, config_name)
        if cached:
            print(f"\n[CACHE] {config_name} - Using cached result from {cached.get('timestamp', 'unknown')}")
            results[config_name] = cached
            continue

        # Execute cleanup via API
        result = await run_cleanup_via_api(
            client, transcription_id, config, token, model_name
        )

        # Cache immediately
        save_to_cache(cache_dir, config_name, result)

        results[config_name] = result

    return results


async def main(model_name: str, case: str):
    """Main execution function."""
    print("Dream Cleanup Testing - API Integration with Database Persistence")
    print("="*60)

    # Load credentials
    email = os.getenv("TEST_USER_EMAIL")
    password = os.getenv("TEST_USER_PASSWORD")

    if not email or not password:
        print("[ERROR] TEST_USER_EMAIL and TEST_USER_PASSWORD must be set in .env")
        print("   Add these lines to your .env file:")
        print("   TEST_USER_EMAIL=your-email@example.com")
        print("   TEST_USER_PASSWORD=your-password")
        return

    cache_dir = get_cache_dir(model_name)

    print(f"Transcription: {TRANSCRIPTION_ID}")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Model: {model_name}")
    print(f"Cache directory: {cache_dir}")
    print(f"Test case: {case}")
    print(f"User: {email}")

    # Create async HTTP client
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Authenticate
        print(f"\n[AUTH] Authenticating...")
        try:
            token = await authenticate(client, email, password)
            print(f"   [OK] Authentication successful!")
        except Exception as e:
            print(f"   [ERROR] Authentication failed: {e}")
            return

        # Run test cases
        all_results = {}

        # Case 1: Temperature only
        if case in ("1", "all"):
            case1_results = await run_test_case(
                "CASE 1: Temperature Only (top_p = null)",
                TEMP_CONFIGS,
                TRANSCRIPTION_ID,
                client,
                token,
                cache_dir,
                model_name
            )
            all_results.update(case1_results)

        # Case 2: Top-p only
        if case in ("2", "all"):
            case2_results = await run_test_case(
                "CASE 2: Top-p Only (temperature = null)",
                TOPP_CONFIGS,
                TRANSCRIPTION_ID,
                client,
                token,
                cache_dir,
                model_name
            )
            all_results.update(case2_results)

        # Case 3: Both parameters
        if case in ("3", "all"):
            case3_results = await run_test_case(
                "CASE 3: Both Parameters (temperature + top_p)",
                BOTH_CONFIGS,
                TRANSCRIPTION_ID,
                client,
                token,
                cache_dir,
                model_name
            )
            all_results.update(case3_results)

        # Save summary
        summary_file = cache_dir / "_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "transcription_id": TRANSCRIPTION_ID,
                "model": model_name,
                "api_base_url": API_BASE_URL,
                "execution_timestamp": datetime.now(timezone.utc).isoformat(),
                "test_case": case,
                "total_configs_executed": len(all_results),
                "configs": list(all_results.keys()),
                "using_api": True,
                "database_persistence": True
            }, f, indent=2)

        print(f"\n{'='*60}")
        print(f"[COMPLETE] Execution complete!")
        print(f"   Total configs processed: {len(all_results)}")
        print(f"   Summary saved to: {summary_file}")
        print(f"   Results saved to database!")
        print(f"   View in frontend or via API:")
        print(f"      GET {API_BASE_URL}/entries/{TRANSCRIPTION_ID}/cleaned")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Execute dream cleanup tests via API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_cleanups_api.py llama-3.3-70b-versatile --case 1   # Temperature only
    python run_cleanups_api.py gpt-oss-120b --case 2              # Top-p only
    python run_cleanups_api.py gpt-oss-120b --case all            # All cases
        """
    )
    parser.add_argument(
        "model",
        type=str,
        help="LLM model name (required). Examples: llama-3.3-70b-versatile, gpt-oss-120b"
    )
    parser.add_argument(
        "--case", "-c",
        choices=["1", "2", "3", "all"],
        default="all",
        help="Test case: 1=Temperature, 2=Top-p, 3=Both, all=All cases (default: all)"
    )

    args = parser.parse_args()
    asyncio.run(main(args.model, args.case))