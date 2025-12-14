"""
Execute transcription tests via journal-service API.

Uses existing entry - does NOT re-upload audio.
Never overwrites results - creates versioned files (v2, v3, ...) if base file exists.

Usage:
    python run_transcriptions.py <entry_id> --provider groq [--temp 0.0]
    python run_transcriptions.py <entry_id> --provider assemblyai

Examples:
    python run_transcriptions.py db1b48a1-59be-49be-bac4-3da3bf8f82cd --provider groq
    python run_transcriptions.py db1b48a1-59be-49be-bac4-3da3bf8f82cd --provider groq --temp 0.5
    python run_transcriptions.py db1b48a1-59be-49be-bac4-3da3bf8f82cd --provider assemblyai

HOW TO RUN:
    cd dream-transcription-testing
    set -a && source ../.env && set +a
    python run_transcriptions.py <entry_id> --provider groq
"""
import asyncio
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

import httpx
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file from project root
load_dotenv(project_root / ".env")

API_BASE_URL = "http://localhost:8000/api/v1"
POLL_INTERVAL = 2  # seconds
MAX_POLL_TIME = 300  # seconds


def get_next_version(cache_dir: Path, base_name: str) -> int:
    """Find next version number. Returns 2 if only base file exists, 3 if v2 exists, etc."""
    pattern = re.compile(rf"^{re.escape(base_name)}_v(\d+)\.json$")
    max_version = 1  # Start at 1 (base file counts as v1)

    if cache_dir.exists():
        for f in cache_dir.iterdir():
            match = pattern.match(f.name)
            if match:
                version = int(match.group(1))
                max_version = max(max_version, version)

    return max_version + 1


def get_cache_path(entry_id: str, provider: str, temperature: Optional[float]) -> Path:
    """Get cache file path. Never overwrites - creates versioned files if base exists."""
    audio_id = entry_id[:8]
    cache_dir = Path(__file__).parent / "cache" / audio_id / provider
    cache_dir.mkdir(parents=True, exist_ok=True)

    if temperature is not None:
        base_name = f"temp_{temperature}"
    else:
        base_name = "result"

    base_file = cache_dir / f"{base_name}.json"

    if not base_file.exists():
        # First run - use base filename
        return base_file
    else:
        # Subsequent runs - create versioned file
        version = get_next_version(cache_dir, base_name)
        return cache_dir / f"{base_name}_v{version}.json"


async def authenticate(client: httpx.AsyncClient, email: str, password: str) -> str:
    """Authenticate and get JWT access token."""
    response = await client.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    response.raise_for_status()
    return response.json()["access_token"]


async def trigger_transcription(
    client: httpx.AsyncClient,
    entry_id: str,
    token: str,
    temperature: Optional[float] = None,
) -> Dict[str, Any]:
    """Trigger transcription on existing entry."""
    headers = {"Authorization": f"Bearer {token}"}

    body = {"language": "sl"}
    if temperature is not None:
        body["temperature"] = temperature

    response = await client.post(
        f"{API_BASE_URL}/entries/{entry_id}/transcribe",
        headers=headers,
        json=body,
        timeout=60.0
    )
    response.raise_for_status()
    return response.json()


async def poll_transcription(
    client: httpx.AsyncClient,
    transcription_id: str,
    token: str,
) -> Dict[str, Any]:
    """Poll transcription status until completed or failed."""
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()

    while True:
        elapsed = time.time() - start_time

        if elapsed > MAX_POLL_TIME:
            raise TimeoutError(f"Timeout after {MAX_POLL_TIME}s")

        response = await client.get(
            f"{API_BASE_URL}/transcriptions/{transcription_id}",
            headers=headers
        )
        response.raise_for_status()
        data = response.json()

        status = data["status"]

        if status == "completed":
            text_length = len(data.get("transcribed_text", ""))
            print(f"   [DONE] {elapsed:.1f}s, {text_length} chars")
            return data
        elif status == "failed":
            print(f"   [FAIL] {data.get('error_message', 'Unknown error')}")
            return data
        else:
            await asyncio.sleep(POLL_INTERVAL)


async def main(entry_id: str, provider: str, temperature: Optional[float]):
    """Main execution function."""
    audio_id = entry_id[:8]

    print("Dream Transcription Testing")
    print("=" * 50)

    # Load credentials
    email = os.getenv("TEST_USER_EMAIL")
    password = os.getenv("TEST_USER_PASSWORD")

    if not email or not password:
        print("[ERROR] TEST_USER_EMAIL and TEST_USER_PASSWORD must be set in .env")
        return

    cache_path = get_cache_path(entry_id, provider, temperature)

    print(f"Entry ID: {entry_id}")
    print(f"Audio ID: {audio_id}")
    print(f"Provider: {provider}")
    print(f"Temperature: {temperature}")
    print(f"Output: {cache_path.name}")

    # Verify provider
    current_provider = os.getenv("TRANSCRIPTION_PROVIDER", "groq").lower().strip('"')
    if current_provider != provider.lower():
        print(f"\n[WARNING] TRANSCRIPTION_PROVIDER={current_provider}, but you requested {provider}")
        print(f"   Run: python switch_provider.py {provider}")
        return

    async with httpx.AsyncClient(timeout=300.0) as client:
        # Authenticate
        print(f"\n[AUTH] Authenticating...")
        try:
            token = await authenticate(client, email, password)
            print(f"   [OK] Authenticated")
        except Exception as e:
            print(f"   [ERROR] {e}")
            return

        # Trigger transcription
        print(f"\n[RUN] Triggering transcription...")
        try:
            trigger_result = await trigger_transcription(
                client=client,
                entry_id=entry_id,
                token=token,
                temperature=temperature,
            )

            transcription_id = trigger_result["transcription_id"]
            print(f"   [OK] Started: {transcription_id[:8]}...")

            trans_result = await poll_transcription(client, transcription_id, token)

            result = {
                "audio_id": audio_id,
                "entry_id": entry_id,
                "provider": provider,
                "temperature": temperature,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "transcription_id": transcription_id,
                "status": trans_result["status"],
                "transcribed_text": trans_result.get("transcribed_text", ""),
                "text_length": len(trans_result.get("transcribed_text", "")),
                "model_used": trans_result.get("model_used", ""),
                "language_detected": trans_result.get("language_code", ""),
                "error_message": trans_result.get("error_message"),
            }

            # Save to cache
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"\n[SAVED] {cache_path}")

        except Exception as e:
            print(f"   [ERROR] {e}")
            return

    print(f"\n{'=' * 50}")
    print(f"Done!")
    print(f"\nCompare: python score.py {audio_id} compare")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run transcription test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_transcriptions.py db1b48a1-59be-49be-bac4-3da3bf8f82cd --provider groq
    python run_transcriptions.py db1b48a1-59be-49be-bac4-3da3bf8f82cd --provider groq --temp 0.5
    python run_transcriptions.py db1b48a1-59be-49be-bac4-3da3bf8f82cd --provider assemblyai
        """
    )
    parser.add_argument("entry_id", help="Entry UUID")
    parser.add_argument("--provider", "-p", required=True, choices=["groq", "assemblyai"])
    parser.add_argument("--temp", "-t", type=float, default=None,
                        help="Temperature (default: 0.0 for groq, ignored for assemblyai)")

    args = parser.parse_args()

    # Default temp to 0.0 for groq, None for assemblyai
    temperature = args.temp
    if temperature is None and args.provider == "groq":
        temperature = 0.0
    elif args.provider == "assemblyai":
        temperature = None

    asyncio.run(main(args.entry_id, args.provider, temperature))
