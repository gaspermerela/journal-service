#!/usr/bin/env python3
"""
Verify all configured transcription providers work correctly.

This script calls the running app's API to test each available provider.
Requires the app to be running at http://localhost:8000.

Usage:
    python scripts/verify_providers.py
    python scripts/verify_providers.py --audio path/to/audio.mp3
    python scripts/verify_providers.py --provider groq  # Test specific provider only
"""
import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

import httpx

BASE_URL = "http://localhost:8000"
DEFAULT_AUDIO = Path("tests/fixtures/crocodile.mp3")


async def check_app_running() -> bool:
    """Check if the app is running."""
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=5) as client:
            response = await client.get("/health")
            return response.status_code == 200
    except httpx.ConnectError:
        return False


async def authenticate(client: httpx.AsyncClient) -> str:
    """Register and login a test user, return access token."""
    email = f"provider_test_{os.urandom(4).hex()}@example.com"
    password = "TestPassword123!"

    # Register
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password}
    )

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )

    if response.status_code != 200:
        raise RuntimeError(f"Login failed: {response.text}")

    return response.json()["access_token"]


async def get_available_providers(client: httpx.AsyncClient) -> list[str]:
    """Get list of available transcription providers from /api/v1/options."""
    response = await client.get("/api/v1/options")
    if response.status_code != 200:
        raise RuntimeError(f"Failed to get options: {response.text}")

    data = response.json()
    return data["transcription"]["available_providers"]


async def wait_for_transcription(
    client: httpx.AsyncClient,
    transcription_id: str,
    max_wait: int = 120,
    poll_interval: int = 3
) -> dict:
    """Poll until transcription completes or fails."""
    start = time.time()

    while time.time() - start < max_wait:
        response = await client.get(f"/api/v1/transcriptions/{transcription_id}")

        if response.status_code != 200:
            raise RuntimeError(f"Failed to get transcription: {response.text}")

        data = response.json()
        status = data.get("status")

        if status == "completed":
            return data
        elif status == "failed":
            raise RuntimeError(f"Transcription failed: {data.get('error_message', 'Unknown error')}")

        await asyncio.sleep(poll_interval)

    raise TimeoutError(f"Transcription did not complete within {max_wait}s")


async def test_provider(
    client: httpx.AsyncClient,
    provider: str,
    audio_path: Path,
    model: str | None = None
) -> dict:
    """
    Test a single provider by uploading audio and transcribing.

    Returns dict with results.
    """
    result = {
        "provider": provider,
        "model": model,
        "success": False,
        "duration_seconds": 0,
        "text_preview": None,
        "error": None
    }

    start = time.time()

    try:
        # Upload audio
        with open(audio_path, "rb") as f:
            files = {"file": (audio_path.name, f, "audio/mpeg")}
            upload_response = await client.post("/api/v1/upload", files=files)

        if upload_response.status_code != 201:
            raise RuntimeError(f"Upload failed: {upload_response.text}")

        entry_id = upload_response.json()["id"]

        # Trigger transcription with specific provider
        transcribe_payload = {
            "language": "en",
            "transcription_provider": provider
        }
        if model:
            transcribe_payload["transcription_model"] = model

        transcribe_response = await client.post(
            f"/api/v1/entries/{entry_id}/transcribe",
            json=transcribe_payload
        )

        if transcribe_response.status_code != 202:
            raise RuntimeError(f"Transcribe failed: {transcribe_response.text}")

        transcription_id = transcribe_response.json()["transcription_id"]

        # Wait for completion
        transcription = await wait_for_transcription(client, transcription_id)

        result["success"] = True
        result["duration_seconds"] = round(time.time() - start, 1)
        text = transcription.get("transcribed_text", "")
        result["text_preview"] = text[:100] + "..." if len(text) > 100 else text

    except Exception as e:
        result["error"] = str(e)
        result["duration_seconds"] = round(time.time() - start, 1)

    return result


async def main():
    parser = argparse.ArgumentParser(description="Verify transcription providers")
    parser.add_argument(
        "--audio",
        type=Path,
        default=DEFAULT_AUDIO,
        help=f"Audio file to use for testing (default: {DEFAULT_AUDIO})"
    )
    parser.add_argument(
        "--provider",
        type=str,
        help="Test specific provider only (default: test all available)"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Specific model to use (for providers with multiple models)"
    )
    args = parser.parse_args()

    # Validate audio file
    if not args.audio.exists():
        print(f"Error: Audio file not found: {args.audio}")
        sys.exit(1)

    # Check app is running
    print(f"Checking app at {BASE_URL}...")
    if not await check_app_running():
        print(f"Error: App not running at {BASE_URL}")
        print("Start the app with: docker compose -f docker-compose.dev.yml up -d")
        sys.exit(1)
    print("App is running\n")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=180) as client:
        # Authenticate
        print("Authenticating...")
        token = await authenticate(client)
        client.headers["Authorization"] = f"Bearer {token}"
        print("Authenticated\n")

        # Get available providers
        available = await get_available_providers(client)
        print(f"Available providers: {', '.join(available)}\n")

        # Filter to specific provider if requested
        if args.provider:
            if args.provider not in available:
                print(f"Error: Provider '{args.provider}' not available")
                print(f"Available: {', '.join(available)}")
                sys.exit(1)
            providers_to_test = [args.provider]
        else:
            # Skip 'noop' in normal testing
            providers_to_test = [p for p in available if p != "noop"]

        if not providers_to_test:
            print("No providers to test (only 'noop' is configured)")
            sys.exit(0)

        # Test each provider
        results = []
        for provider in providers_to_test:
            print(f"Testing {provider}...")
            result = await test_provider(
                client,
                provider,
                args.audio,
                model=args.model if args.provider else None
            )
            results.append(result)

            if result["success"]:
                print(f"  OK ({result['duration_seconds']}s)")
                print(f"  Preview: {result['text_preview']}")
            else:
                print(f"  FAILED: {result['error']}")
            print()

        # Summary
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)

        passed = sum(1 for r in results if r["success"])
        failed = len(results) - passed

        for r in results:
            status = "PASS" if r["success"] else "FAIL"
            model_str = f" ({r['model']})" if r["model"] else ""
            print(f"  [{status}] {r['provider']}{model_str} - {r['duration_seconds']}s")

        print()
        print(f"Passed: {passed}/{len(results)}")

        if failed > 0:
            print(f"Failed: {failed}/{len(results)}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
