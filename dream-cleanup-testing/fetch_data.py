"""
Fetch transcription and prompt data for cleanup testing.

Uses a hybrid approach:
- Prompts: Fetched directly from DB (stored as plaintext)
- Transcriptions: Fetched via API (encrypted in DB, decrypted by API)

Usage:
    python fetch_data.py --prompt <prompt_name>

Examples:
    python fetch_data.py --prompt dream_v8
    python fetch_data.py --prompt dream_v5

Cache Structure:
    Data is saved per prompt version:
    cache/{transcription_id}/{prompt_name}/fetched_data.json

    This allows different prompts to be tested independently, each with
    its own fetched_data.json containing the exact prompt text used.

HOW TO RUN:
    From the dream-cleanup-testing directory, source .env first to export environment variables:

    cd dream-cleanup-testing
    set -a && source ../.env && set +a && python fetch_data.py --prompt dream_v8

    This exports DATABASE_PASSWORD, JWT_SECRET_KEY, TEST_USER_EMAIL, TEST_USER_PASSWORD,
    and other required env vars before running.
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file from project root
load_dotenv(project_root / ".env")

# Direct DB access for prompts (not encrypted)
from app.database import get_session
from sqlalchemy import select
# Import all models to ensure SQLAlchemy relationships are properly initialized
from app.models.user import User
from app.models.user_preference import UserPreference
from app.models.voice_entry import VoiceEntry
from app.models.transcription import Transcription
from app.models.cleaned_entry import CleanedEntry
from app.models.prompt_template import PromptTemplate
from app.models.notion_sync import NotionSync

# Configuration
TRANSCRIPTION_ID = "50e135d5-5045-4bce-a36d-a72e316b782e"
API_BASE_URL = "http://localhost:8000/api/v1"


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


async def fetch_transcription_data(prompt_name: str):
    """
    Fetch the target transcription and specified prompt data.

    Uses hybrid approach:
    - Prompts: Direct DB access (stored as plaintext)
    - Transcriptions: API access (encrypted in DB, decrypted by API)
    """
    # Get credentials from environment
    email = os.getenv("TEST_USER_EMAIL")
    password = os.getenv("TEST_USER_PASSWORD")

    if not email or not password:
        print("❌ ERROR: TEST_USER_EMAIL and TEST_USER_PASSWORD must be set in .env")
        print("   These are required to authenticate with the API.")
        return None

    # 1. Fetch prompt directly from DB (NOT encrypted - plaintext Text column)
    async with get_session() as db:
        stmt = (
            select(PromptTemplate)
            .where(PromptTemplate.name == prompt_name)
            .order_by(PromptTemplate.version.desc())
        )
        result = await db.execute(stmt)
        prompt = result.scalars().first()

        if not prompt:
            print(f"❌ ERROR: No prompt found with name '{prompt_name}'!")
            # List available prompts
            stmt = select(PromptTemplate.name, PromptTemplate.version).distinct()
            result = await db.execute(stmt)
            available = result.all()
            print(f"\n📋 Available prompts:")
            for name, version in available:
                print(f"   - {name} (v{version})")
            return None

    # 2. Fetch transcription via API (encrypted in DB, decrypted by API)
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Authenticate
            print("🔐 Authenticating with API...")
            token = await authenticate(client, email, password)
            headers = {"Authorization": f"Bearer {token}"}

            # Fetch transcription (API decrypts automatically)
            print(f"📥 Fetching transcription {TRANSCRIPTION_ID} via API...")
            response = await client.get(
                f"{API_BASE_URL}/transcriptions/{TRANSCRIPTION_ID}",
                headers=headers
            )
            response.raise_for_status()
            transcription_data = response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"❌ ERROR: Transcription {TRANSCRIPTION_ID} not found!")
            elif e.response.status_code == 401:
                print(f"❌ ERROR: Authentication failed. Check TEST_USER_EMAIL/PASSWORD.")
            else:
                print(f"❌ ERROR: API request failed: {e}")
            return None
        except httpx.ConnectError:
            print("❌ ERROR: Could not connect to API. Is the server running?")
            print(f"   Expected at: {API_BASE_URL}")
            return None

    # Extract transcription text (already decrypted by API)
    transcription_text = transcription_data.get("transcribed_text", "")

    if not transcription_text:
        print(f"❌ ERROR: Transcription has no text (status: {transcription_data.get('status')})")
        return None

    # Print data
    print(f"\n=== TRANSCRIPTION DATA ===")
    print(f"ID: {transcription_data['id']}")
    print(f"Status: {transcription_data['status']}")
    print(f"Model: {transcription_data.get('model_used', 'N/A')}")
    print(f"Language: {transcription_data.get('language_code', 'N/A')}")
    print(f"\nText length: {len(transcription_text)} characters")
    print(f"\n=== TRANSCRIPTION TEXT ===\n{transcription_text}\n")

    print(f"\n=== PROMPT ({prompt_name}) ===")
    print(f"ID: {prompt.id}")
    print(f"Name: {prompt.name}")
    print(f"Version: {prompt.version}")
    print(f"Entry Type: {prompt.entry_type}")
    print(f"\n=== PROMPT TEXT ===\n{prompt.prompt_text}\n")

    return {
        "transcription": {
            "id": str(transcription_data["id"]),
            "text": transcription_text,
            "model": transcription_data.get("model_used", ""),
            "language": transcription_data.get("language_code", ""),
            "created_at": str(transcription_data.get("created_at", ""))
        },
        "prompt": {
            "id": prompt.id,
            "name": prompt.name,
            "version": prompt.version,
            "text": prompt.prompt_text,
            "entry_type": prompt.entry_type
        }
    }


def main(prompt_name: str):
    """Main execution function."""
    data = asyncio.run(fetch_transcription_data(prompt_name))

    if data:
        # Save to prompt-specific directory
        # Structure: cache/{transcription_id}/{prompt_name}/fetched_data.json
        transcription_id = data["transcription"]["id"]
        cache_dir = Path(__file__).parent / "cache" / transcription_id / prompt_name
        cache_dir.mkdir(parents=True, exist_ok=True)
        output_file = cache_dir / "fetched_data.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Data saved to: {output_file}")
        print(f"\n📝 To run tests with this prompt:")
        print(f"   python run_cleanups_api.py llama-3.3-70b-versatile --prompt {prompt_name} --case 1")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch transcription and prompt data from database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python fetch_data.py --prompt dream_v8
    python fetch_data.py --prompt dream_v5
        """
    )
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        required=True,
        help="Prompt name to fetch (required). Examples: dream_v5, dream_v7, dream_v8"
    )

    args = parser.parse_args()
    main(args.prompt)