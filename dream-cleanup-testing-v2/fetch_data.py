"""
Fetch transcription and prompt data from database for cleanup testing.

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
    From the dream-cleanup-testing-v2 directory, source .env first to export environment variables:

    cd dream-cleanup-testing-v2
    set -a && source ../.env && set +a && python fetch_data.py --prompt dream_v8

    This exports DATABASE_PASSWORD, JWT_SECRET_KEY, and other required env vars before running.
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import get_session
from sqlalchemy import select
# Import all models to ensure relationships work
from app.models.user import User
from app.models.user_preference import UserPreference
from app.models.voice_entry import VoiceEntry
from app.models.transcription import Transcription
from app.models.cleaned_entry import CleanedEntry
from app.models.prompt_template import PromptTemplate
from app.models.notion_sync import NotionSync
import json

# Configuration
TRANSCRIPTION_ID = "5beeaea1-967a-4569-9c84-eccad8797b95"


async def fetch_transcription_data(prompt_name: str):
    """Fetch the target transcription and specified prompt data."""

    async with get_session() as db:
        # Fetch specific transcription
        stmt = select(Transcription).where(Transcription.id == TRANSCRIPTION_ID)
        result = await db.execute(stmt)
        transcription = result.scalar_one_or_none()

        if not transcription:
            print(f"❌ ERROR: Transcription {TRANSCRIPTION_ID} not found!")
            return None

        # Fetch prompt by name
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

        # Print data
        print(f"=== TRANSCRIPTION DATA ===")
        print(f"ID: {transcription.id}")
        print(f"Status: {transcription.status}")
        print(f"Model: {transcription.model_used}")
        print(f"Language: {transcription.language_code}")
        print(f"Created: {transcription.created_at}")
        print(f"\nText length: {len(transcription.transcribed_text)} characters")
        print(f"\n=== TRANSCRIPTION TEXT ===\n{transcription.transcribed_text}\n")

        print(f"\n=== PROMPT ({prompt_name}) ===")
        print(f"ID: {prompt.id}")
        print(f"Name: {prompt.name}")
        print(f"Version: {prompt.version}")
        print(f"Entry Type: {prompt.entry_type}")
        print(f"\n=== PROMPT TEXT ===\n{prompt.prompt_text}\n")

        return {
            "transcription": {
                "id": str(transcription.id),
                "text": transcription.transcribed_text,
                "model": transcription.model_used,
                "language": transcription.language_code,
                "created_at": str(transcription.created_at)
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