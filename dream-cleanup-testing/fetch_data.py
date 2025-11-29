"""
Fetch transcription and prompt data from database for cleanup testing.
"""
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


async def fetch_transcription_data():
    """Fetch the target transcription data."""
    transcription_id = "5beeaea1-967a-4569-9c84-eccad8797b95"

    async with get_session() as db:
        # Fetch specific transcription
        stmt = select(Transcription).where(Transcription.id == transcription_id)
        result = await db.execute(stmt)
        transcription = result.scalar_one_or_none()

        if not transcription:
            print(f"ERROR: Transcription {transcription_id} not found!")
            return None

        # Fetch active prompt for "dream" entry type
        entry_type = "dream"
        stmt = (
            select(PromptTemplate)
            .where(
                PromptTemplate.entry_type == entry_type,
                PromptTemplate.is_active == True
            )
            .order_by(PromptTemplate.updated_at.desc())
        )
        result = await db.execute(stmt)
        active_prompt = result.scalars().first()

        if not active_prompt:
            print(f"ERROR: No active prompt found for entry_type '{entry_type}'!")
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

        print(f"\n=== ACTIVE PROMPT ===")
        print(f"ID: {active_prompt.id}")
        print(f"Name: {active_prompt.name}")
        print(f"Version: {active_prompt.version}")
        print(f"Entry Type: {active_prompt.entry_type}")
        print(f"\n=== PROMPT TEXT ===\n{active_prompt.prompt_text}\n")

        return {
            "transcription": {
                "id": str(transcription.id),
                "text": transcription.transcribed_text,
                "model": transcription.model_used,
                "language": transcription.language_code,
                "created_at": str(transcription.created_at)
            },
            "prompt": {
                "id": active_prompt.id,
                "name": active_prompt.name,
                "version": active_prompt.version,
                "text": active_prompt.prompt_text,
                "entry_type": active_prompt.entry_type
            }
        }


if __name__ == "__main__":
    data = asyncio.run(fetch_transcription_data())

    if data:
        # Save to JSON for easy access
        output_file = Path(__file__).parent / "cache" / "fetched_data.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Data saved to: {output_file}")