"""
Tests for LLM cleanup service prompt loading and fallback mechanisms.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm_cleanup_ollama import OllamaLLMCleanupService
from app.models.prompt_template import PromptTemplate


# Alias for backward compatibility with tests
LLMCleanupService = OllamaLLMCleanupService


class TestPromptFallbackMechanisms:
    """Test fallback chain for prompt template loading."""

    @pytest.mark.asyncio
    async def test_get_prompt_from_db_success(self):
        """Test successfully loading prompt from database."""
        # Create mock session
        mock_session = AsyncMock(spec=AsyncSession)

        # Create mock prompt template
        mock_template = PromptTemplate(
            id=1,
            name="test_prompt",
            entry_type="dream",
            prompt_text="Test prompt with {transcription_text} placeholder",
            description="Test prompt",
            is_active=True,
            version=1
        )

        # Mock database query chain: execute() -> scalars() -> first()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = mock_template

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_session.execute.return_value = mock_result

        # Create service with mocked session
        service = OllamaLLMCleanupService(db_session=mock_session)

        # Test DB prompt loading
        result = await service._get_prompt_from_db("dream")

        assert result is not None
        prompt_text, template_id = result
        assert "{transcription_text}" in prompt_text
        assert template_id == 1

    @pytest.mark.asyncio
    async def test_get_prompt_from_db_no_active_prompt(self):
        """Test when no active prompt exists in database."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock no results: execute() -> scalars() -> first() returns None
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_session.execute.return_value = mock_result

        service = LLMCleanupService(db_session=mock_session)

        result = await service._get_prompt_from_db("dream")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_prompt_from_db_invalid_template(self):
        """Test when active prompt template is invalid."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Create invalid template (missing placeholder)
        mock_template = PromptTemplate(
            id=2,
            name="invalid_prompt",
            entry_type="dream",
            prompt_text="Invalid prompt without placeholder",
            description="Invalid",
            is_active=True,
            version=1
        )

        # Mock database query chain: execute() -> scalars() -> first()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = mock_template

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_session.execute.return_value = mock_result

        service = LLMCleanupService(db_session=mock_session)

        result = await service._get_prompt_from_db("dream")

        # Should return None because template is invalid
        assert result is None

    @pytest.mark.asyncio
    async def test_get_prompt_from_db_no_session(self):
        """Test when no database session provided."""
        service = LLMCleanupService(db_session=None)

        result = await service._get_prompt_from_db("dream")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_prompt_from_db_exception(self):
        """Test when database query raises exception."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute.side_effect = Exception("Database error")

        service = LLMCleanupService(db_session=mock_session)

        result = await service._get_prompt_from_db("dream")

        # Should return None on exception
        assert result is None

    def test_hardcoded_fallback_prompt_dream(self):
        """Test hardcoded fallback for dream entry type."""
        service = LLMCleanupService()

        prompt = service._get_hardcoded_fallback_prompt("dream")

        assert "dream journal assistant" in prompt.lower()
        assert "{transcription_text}" in prompt

    def test_hardcoded_fallback_prompt_generic(self):
        """Test hardcoded fallback for non-dream entry types."""
        service = LLMCleanupService()

        for entry_type in ["journal", "meeting", "note"]:
            prompt = service._get_hardcoded_fallback_prompt(entry_type)

            assert "transcription cleanup assistant" in prompt.lower()
            assert "{transcription_text}" in prompt

    @pytest.mark.asyncio
    async def test_get_prompt_template_with_db_success(self):
        """Test full prompt template chain with successful DB lookup."""
        mock_session = AsyncMock(spec=AsyncSession)

        mock_template = PromptTemplate(
            id=5,
            name="custom_prompt",
            entry_type="journal",
            prompt_text="Custom prompt for {transcription_text}",
            description="Custom",
            is_active=True,
            version=2
        )

        # Mock database query chain: execute() -> scalars() -> first()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = mock_template

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_session.execute.return_value = mock_result

        service = LLMCleanupService(db_session=mock_session)

        prompt_text, template_id = await service._get_prompt_template("journal")

        assert "Custom prompt for" in prompt_text
        assert template_id == 5

    @pytest.mark.asyncio
    async def test_get_prompt_template_fallback_to_hardcoded(self):
        """Test fallback to hardcoded prompt when DB lookup fails."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock no results: execute() -> scalars() -> first() returns None
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_session.execute.return_value = mock_result

        service = LLMCleanupService(db_session=mock_session)

        prompt_text, template_id = await service._get_prompt_template("dream")

        # Should fall back to hardcoded prompt
        assert "dream journal assistant" in prompt_text.lower()
        assert template_id is None  # No DB template used

    @pytest.mark.asyncio
    async def test_get_prompt_template_no_session_uses_fallback(self):
        """Test using hardcoded fallback when no session provided."""
        service = LLMCleanupService(db_session=None)

        prompt_text, template_id = await service._get_prompt_template("journal")

        # Should use hardcoded fallback
        assert "transcription cleanup assistant" in prompt_text.lower()
        assert template_id is None


class TestPromptTemplateValidation:
    """Test PromptTemplate.is_valid property."""

    def test_valid_prompt_template(self):
        """Test valid prompt template."""
        template = PromptTemplate(
            id=1,
            name="valid",
            entry_type="dream",
            prompt_text="Valid prompt with {transcription_text} placeholder",
            is_active=True,
            version=1
        )

        assert template.is_valid is True

    def test_invalid_prompt_template_no_placeholder(self):
        """Test invalid prompt template missing placeholder."""
        template = PromptTemplate(
            id=2,
            name="invalid",
            entry_type="dream",
            prompt_text="Missing placeholder",
            is_active=True,
            version=1
        )

        assert template.is_valid is False

    def test_invalid_prompt_template_empty_text(self):
        """Test invalid prompt template with empty text."""
        template = PromptTemplate(
            id=3,
            name="empty",
            entry_type="dream",
            prompt_text="",
            is_active=True,
            version=1
        )

        assert template.is_valid is False

    def test_invalid_prompt_template_none_text(self):
        """Test invalid prompt template with None text."""
        template = PromptTemplate(
            id=4,
            name="none",
            entry_type="dream",
            prompt_text=None,
            is_active=True,
            version=1
        )

        assert template.is_valid is False
