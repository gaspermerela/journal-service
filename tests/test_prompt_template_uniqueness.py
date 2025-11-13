"""
Integration tests for prompt template uniqueness constraint.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update

from app.services.database import DatabaseService
from app.models.prompt_template import PromptTemplate


@pytest.fixture
def db_service():
    """Create database service instance."""
    return DatabaseService()


@pytest.mark.asyncio
async def test_only_one_active_prompt_per_entry_type(db_session: AsyncSession):
    """Test that only one prompt can be active per entry_type at database level."""
    # Create two prompts for the same entry_type
    prompt1 = PromptTemplate(
        name="test_v1",
        entry_type="test_type",
        prompt_text="Test prompt 1 with {transcription_text}",
        description="First test prompt",
        is_active=True,
        version=1
    )
    db_session.add(prompt1)
    await db_session.flush()

    # Try to create a second active prompt for the same entry_type
    prompt2 = PromptTemplate(
        name="test_v2",
        entry_type="test_type",
        prompt_text="Test prompt 2 with {transcription_text}",
        description="Second test prompt",
        is_active=True,
        version=2
    )
    db_session.add(prompt2)

    # Should raise IntegrityError due to unique constraint
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_multiple_inactive_prompts_allowed(db_session: AsyncSession):
    """Test that multiple inactive prompts for the same entry_type are allowed."""
    # Create multiple inactive prompts for the same entry_type
    prompt1 = PromptTemplate(
        name="test_v1",
        entry_type="test_type",
        prompt_text="Test prompt 1 with {transcription_text}",
        description="First test prompt",
        is_active=False,
        version=1
    )
    prompt2 = PromptTemplate(
        name="test_v2",
        entry_type="test_type",
        prompt_text="Test prompt 2 with {transcription_text}",
        description="Second test prompt",
        is_active=False,
        version=2
    )
    prompt3 = PromptTemplate(
        name="test_v3",
        entry_type="test_type",
        prompt_text="Test prompt 3 with {transcription_text}",
        description="Third test prompt",
        is_active=False,
        version=3
    )

    db_session.add_all([prompt1, prompt2, prompt3])
    await db_session.flush()

    # All should be created successfully
    assert prompt1.id is not None
    assert prompt2.id is not None
    assert prompt3.id is not None


@pytest.mark.asyncio
async def test_different_entry_types_can_both_be_active(db_session: AsyncSession):
    """Test that different entry types can each have an active prompt."""
    # First, deactivate any existing active prompts for these entry types
    await db_session.execute(
        update(PromptTemplate)
        .where(PromptTemplate.entry_type.in_(["dream", "journal"]))
        .values(is_active=False)
    )
    await db_session.flush()

    # Create active prompts for different entry types
    prompt_dream = PromptTemplate(
        name="test_dream_unique",
        entry_type="dream",
        prompt_text="Dream prompt with {transcription_text}",
        description="Dream prompt",
        is_active=True,
        version=1
    )
    prompt_journal = PromptTemplate(
        name="test_journal_unique",
        entry_type="journal",
        prompt_text="Journal prompt with {transcription_text}",
        description="Journal prompt",
        is_active=True,
        version=1
    )

    db_session.add_all([prompt_dream, prompt_journal])
    await db_session.flush()

    # Both should be created successfully
    assert prompt_dream.id is not None
    assert prompt_journal.id is not None
    assert prompt_dream.is_active is True
    assert prompt_journal.is_active is True


@pytest.mark.asyncio
async def test_activate_prompt_template_deactivates_others(
    db_session: AsyncSession,
    db_service: DatabaseService
):
    """Test that activating a prompt deactivates others for the same entry_type."""
    # Create multiple inactive prompts
    prompt1 = PromptTemplate(
        name="test_v1",
        entry_type="test_type",
        prompt_text="Test prompt 1 with {transcription_text}",
        description="First test prompt",
        is_active=True,
        version=1
    )
    prompt2 = PromptTemplate(
        name="test_v2",
        entry_type="test_type",
        prompt_text="Test prompt 2 with {transcription_text}",
        description="Second test prompt",
        is_active=False,
        version=2
    )

    db_session.add_all([prompt1, prompt2])
    await db_session.flush()

    # Activate the second prompt
    activated = await db_service.activate_prompt_template(db_session, prompt2.id)

    await db_session.refresh(prompt1)
    await db_session.refresh(prompt2)

    # Verify that prompt2 is active and prompt1 is inactive
    assert prompt2.is_active is True
    assert prompt1.is_active is False
    assert activated.id == prompt2.id


@pytest.mark.asyncio
async def test_activate_prompt_template_does_not_affect_other_entry_types(
    db_session: AsyncSession,
    db_service: DatabaseService
):
    """Test that activating a prompt doesn't affect prompts for different entry types."""
    # First, deactivate any existing active prompts for these entry types
    await db_session.execute(
        update(PromptTemplate)
        .where(PromptTemplate.entry_type.in_(["dream", "journal"]))
        .values(is_active=False)
    )
    await db_session.flush()

    # Create prompts for different entry types
    prompt_dream = PromptTemplate(
        name="test_dream_activation",
        entry_type="dream",
        prompt_text="Dream prompt with {transcription_text}",
        description="Dream prompt",
        is_active=True,
        version=1
    )
    prompt_journal_v1 = PromptTemplate(
        name="test_journal_v1_activation",
        entry_type="journal",
        prompt_text="Journal prompt v1 with {transcription_text}",
        description="Journal prompt v1",
        is_active=True,
        version=1
    )
    prompt_journal_v2 = PromptTemplate(
        name="test_journal_v2_activation",
        entry_type="journal",
        prompt_text="Journal prompt v2 with {transcription_text}",
        description="Journal prompt v2",
        is_active=False,
        version=2
    )

    db_session.add_all([prompt_dream, prompt_journal_v1, prompt_journal_v2])
    await db_session.flush()

    # Activate journal v2
    await db_service.activate_prompt_template(db_session, prompt_journal_v2.id)

    await db_session.refresh(prompt_dream)
    await db_session.refresh(prompt_journal_v1)
    await db_session.refresh(prompt_journal_v2)

    # Dream prompt should still be active
    assert prompt_dream.is_active is True
    # Journal v2 should be active, v1 inactive
    assert prompt_journal_v2.is_active is True
    assert prompt_journal_v1.is_active is False


@pytest.mark.asyncio
async def test_activate_nonexistent_prompt_raises_error(
    db_session: AsyncSession,
    db_service: DatabaseService
):
    """Test that activating a non-existent prompt raises an error."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await db_service.activate_prompt_template(db_session, 99999)

    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail).lower()
