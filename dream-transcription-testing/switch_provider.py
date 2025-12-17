"""
Switch transcription provider: updates .env, restarts app, waits for health.

Usage:
    python switch_provider.py <groq|assemblyai>

Examples:
    python switch_provider.py groq
    python switch_provider.py assemblyai
"""
import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

import httpx

VALID_PROVIDERS = ["groq", "assemblyai", "whisper", "clarinsi_slovene_asr"]
HEALTH_URL = "http://localhost:8000/health"
HEALTH_TIMEOUT = 12  # Actual startup ~5s, with 100% buffer
PROJECT_ROOT = Path(__file__).parent.parent


def kill_port_8000():
    """Kill any process on port 8000."""
    print("[STOP] Killing port 8000...")
    result = subprocess.run(
        "lsof -ti:8000 | xargs kill -9 2>/dev/null || true",
        shell=True,
        capture_output=True
    )
    time.sleep(1)
    print("   [OK] Port 8000 cleared")


def update_env_file(provider: str) -> bool:
    """Update TRANSCRIPTION_PROVIDER in .env file."""
    env_file = PROJECT_ROOT / ".env"

    if not env_file.exists():
        print(f"[ERROR] .env file not found: {env_file}")
        return False

    content = env_file.read_text()

    if "TRANSCRIPTION_PROVIDER=" in content:
        new_content = re.sub(
            r'TRANSCRIPTION_PROVIDER="?\w+"?',
            f'TRANSCRIPTION_PROVIDER="{provider}"',
            content
        )
    else:
        new_content = content + f'\nTRANSCRIPTION_PROVIDER="{provider}"\n'

    env_file.write_text(new_content)
    print(f"[ENV] Updated: TRANSCRIPTION_PROVIDER={provider}")
    return True


def start_app():
    """Start the app in background."""
    print("[START] Starting app...")
    subprocess.Popen(
        f"set -a && source .env && set +a && python -m app.main > /tmp/journal-app.log 2>&1",
        shell=True,
        cwd=PROJECT_ROOT,
        start_new_session=True
    )
    print("   [OK] App starting (logs: /tmp/journal-app.log)")


def wait_for_health() -> bool:
    """Wait for health check to pass."""
    print(f"[HEALTH] Waiting for {HEALTH_URL}...")
    start_time = time.time()

    while time.time() - start_time < HEALTH_TIMEOUT:
        try:
            response = httpx.get(HEALTH_URL, timeout=2.0)
            if response.status_code == 200:
                elapsed = time.time() - start_time
                print(f"   [OK] Healthy ({elapsed:.1f}s)")
                return True
        except httpx.RequestError:
            pass
        time.sleep(1)

    print(f"[ERROR] Health check timed out after {HEALTH_TIMEOUT}s")
    print("   Check logs: cat /tmp/journal-app.log")
    return False


def main(provider: str):
    """Main execution."""
    print("=" * 50)
    print(f"Switching to: {provider}")
    print("=" * 50)

    if provider.lower() not in VALID_PROVIDERS:
        print(f"[ERROR] Invalid provider: {provider}")
        print(f"   Valid: {', '.join(VALID_PROVIDERS)}")
        sys.exit(1)

    kill_port_8000()

    if not update_env_file(provider):
        sys.exit(1)

    start_app()

    if not wait_for_health():
        sys.exit(1)

    print("=" * 50)
    print(f"[DONE] Provider: {provider}")
    print(f"\nRun tests:")
    print(f"   python run_transcriptions.py <audio_id> --provider {provider}")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Switch transcription provider")
    parser.add_argument("provider", choices=VALID_PROVIDERS, help="Provider to use")
    args = parser.parse_args()
    main(args.provider)