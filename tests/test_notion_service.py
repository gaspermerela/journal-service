"""
Unit tests for NotionService.

Tests Notion API integration with mocked responses.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from notion_client.errors import APIResponseError

from app.services.notion_service import (
    NotionService,
    NotionError,
    NotionValidationError,
    NotionAPIError
)


@pytest.fixture
def mock_notion_client():
    """Create a mock Notion client."""
    with patch("app.services.notion_service.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_rate_limiter():
    """Create a mock rate limiter that doesn't actually rate limit."""
    with patch("app.services.notion_service.get_rate_limiter") as mock_get_limiter:
        mock_limiter = AsyncMock()
        mock_limiter.__aenter__ = AsyncMock(return_value=mock_limiter)
        mock_limiter.__aexit__ = AsyncMock(return_value=None)
        mock_get_limiter.return_value = mock_limiter
        yield mock_limiter


@pytest.fixture
def notion_service(mock_notion_client, mock_rate_limiter):
    """Create a NotionService instance with mocked dependencies."""
    return NotionService(api_key="test_api_key")


@pytest.mark.asyncio
async def test_validate_database_success(notion_service, mock_notion_client):
    """Test successful database validation."""
    # Mock database response (no properties field)
    mock_database = {
        "id": "test_db_id",
        "title": [{"plain_text": "Dream Journal"}],
        "data_sources": [{"id": "data_source_123"}]
    }
    mock_notion_client.databases.retrieve = AsyncMock(return_value=mock_database)

    # Mock data source response with properties
    mock_data_source = {
        "id": "data_source_123",
        "properties": {
            "Name": {"type": "title"},
            "Date": {"type": "date"},
            "Wake Time": {"type": "rich_text"}
        }
    }
    mock_notion_client.data_sources.retrieve = AsyncMock(return_value=mock_data_source)

    # Validate database
    result = await notion_service.validate_database("test_db_id")

    # Verify both API calls were made
    mock_notion_client.databases.retrieve.assert_called_once_with(database_id="test_db_id")
    mock_notion_client.data_sources.retrieve.assert_called_once_with(data_source_id="data_source_123")

    # Verify result combines database with properties from data source
    assert result["id"] == "test_db_id"
    assert result["title"] == [{"plain_text": "Dream Journal"}]
    assert result["properties"] == mock_data_source["properties"]


@pytest.mark.asyncio
async def test_validate_database_missing_property(notion_service, mock_notion_client):
    """Test database validation fails when required property is missing."""
    # Mock database response
    mock_database = {
        "id": "test_db_id",
        "title": [{"plain_text": "Dream Journal"}],
        "data_sources": [{"id": "data_source_123"}]
    }
    mock_notion_client.databases.retrieve = AsyncMock(return_value=mock_database)

    # Mock data source missing "Wake Time" property
    mock_data_source = {
        "id": "data_source_123",
        "properties": {
            "Name": {"type": "title"},
            "Date": {"type": "date"}
            # Missing: Wake Time
        }
    }
    mock_notion_client.data_sources.retrieve = AsyncMock(return_value=mock_data_source)

    # Should raise validation error
    with pytest.raises(NotionValidationError, match="missing properties: Wake Time"):
        await notion_service.validate_database("test_db_id")


@pytest.mark.asyncio
async def test_validate_database_wrong_property_type(notion_service, mock_notion_client):
    """Test database validation fails when property has wrong type."""
    # Mock database response
    mock_database = {
        "id": "test_db_id",
        "title": [{"plain_text": "Dream Journal"}],
        "data_sources": [{"id": "data_source_123"}]
    }
    mock_notion_client.databases.retrieve = AsyncMock(return_value=mock_database)

    # Mock data source with wrong type for "Date" (should be date, not rich_text)
    mock_data_source = {
        "id": "data_source_123",
        "properties": {
            "Name": {"type": "title"},
            "Date": {"type": "rich_text"},  # Wrong type
            "Wake Time": {"type": "rich_text"}
        }
    }
    mock_notion_client.data_sources.retrieve = AsyncMock(return_value=mock_data_source)

    # Should raise validation error
    with pytest.raises(NotionValidationError, match="wrong property types.*Date.*expected date"):
        await notion_service.validate_database("test_db_id")


@pytest.mark.asyncio
async def test_validate_database_no_data_sources(notion_service, mock_notion_client):
    """Test database validation fails when database has no data sources."""
    # Mock database with no data sources
    mock_database = {
        "id": "test_db_id",
        "title": [{"plain_text": "Dream Journal"}],
        "data_sources": []  # Empty data sources
    }
    mock_notion_client.databases.retrieve = AsyncMock(return_value=mock_database)

    # Should raise validation error
    with pytest.raises(NotionValidationError, match="Database has no data sources"):
        await notion_service.validate_database("test_db_id")


@pytest.mark.asyncio
async def test_validate_database_api_error(notion_service, mock_notion_client):
    """Test database validation handles API errors."""
    # Mock API error (e.g., invalid database ID, no access, etc.)
    mock_notion_client.databases.retrieve = AsyncMock(
        side_effect=APIResponseError(
            response=MagicMock(status_code=404),
            message="Database not found",
            code="object_not_found"
        )
    )

    # Should raise NotionAPIError
    with pytest.raises(NotionAPIError, match="Failed to validate database"):
        await notion_service.validate_database("invalid_db_id")


@pytest.mark.asyncio
async def test_create_dream_page_success(notion_service, mock_notion_client):
    """Test successful dream page creation."""
    # Mock successful page creation
    mock_page = {
        "id": "page_123",
        "url": "https://notion.so/page_123"
    }
    mock_notion_client.pages.create = AsyncMock(return_value=mock_page)

    # Create page
    uploaded_at = datetime(2025, 1, 15, 4, 30, tzinfo=timezone.utc)
    result = await notion_service.create_dream_page(
        database_id="db_123",
        dream_content="I was flying over mountains...",
        uploaded_at=uploaded_at,
        dream_name="Lucid Flight"
    )

    # Verify
    assert result == mock_page
    mock_notion_client.pages.create.assert_called_once()

    # Check call arguments
    call_args = mock_notion_client.pages.create.call_args
    assert call_args.kwargs["parent"]["database_id"] == "db_123"

    # Check properties
    properties = call_args.kwargs["properties"]
    assert properties["Name"]["title"][0]["text"]["content"] == "Lucid Flight"
    assert properties["Date"]["date"]["start"] == "2025-01-15"
    assert properties["Wake Time"]["rich_text"][0]["text"]["content"] == "04:30"

    # Check content
    children = call_args.kwargs["children"]
    assert children[0]["paragraph"]["rich_text"][0]["text"]["content"] == "I was flying over mountains..."


@pytest.mark.asyncio
async def test_create_dream_page_default_name(notion_service, mock_notion_client):
    """Test dream page creation with default name."""
    mock_page = {"id": "page_123", "url": "https://notion.so/page_123"}
    mock_notion_client.pages.create = AsyncMock(return_value=mock_page)

    # Create page without custom name
    uploaded_at = datetime(2025, 1, 15, 4, 30, tzinfo=timezone.utc)
    await notion_service.create_dream_page(
        database_id="db_123",
        dream_content="Dream content",
        uploaded_at=uploaded_at
    )

    # Verify default name is "Dream"
    call_args = mock_notion_client.pages.create.call_args
    properties = call_args.kwargs["properties"]
    assert properties["Name"]["title"][0]["text"]["content"] == "Dream"


@pytest.mark.asyncio
async def test_create_dream_page_api_error(notion_service, mock_notion_client):
    """Test dream page creation handles API errors."""
    # Mock API error
    mock_notion_client.pages.create = AsyncMock(
        side_effect=APIResponseError(
            response=MagicMock(status_code=400),
            message="Invalid request",
            code="validation_error"
        )
    )

    # Should raise NotionAPIError
    uploaded_at = datetime(2025, 1, 15, 4, 30, tzinfo=timezone.utc)
    with pytest.raises(NotionAPIError, match="Failed to create page"):
        await notion_service.create_dream_page(
            database_id="db_123",
            dream_content="Dream content",
            uploaded_at=uploaded_at
        )


@pytest.mark.asyncio
async def test_update_dream_page_name_only(notion_service, mock_notion_client):
    """Test updating only the dream name."""
    mock_page = {"id": "page_123", "url": "https://notion.so/page_123"}
    mock_notion_client.pages.update = AsyncMock(return_value=mock_page)

    # Update only name
    result = await notion_service.update_dream_page(
        page_id="page_123",
        dream_name="Updated Dream Title"
    )

    # Verify
    assert result == mock_page
    call_args = mock_notion_client.pages.update.call_args
    assert call_args.kwargs["page_id"] == "page_123"

    properties = call_args.kwargs["properties"]
    assert properties["Name"]["title"][0]["text"]["content"] == "Updated Dream Title"
    assert "Date" not in properties
    assert "Wake Time" not in properties


@pytest.mark.asyncio
async def test_update_dream_page_timestamp(notion_service, mock_notion_client):
    """Test updating date and wake time."""
    mock_page = {"id": "page_123", "url": "https://notion.so/page_123"}
    mock_notion_client.pages.update = AsyncMock(return_value=mock_page)

    # Update timestamp
    new_time = datetime(2025, 2, 20, 6, 15, tzinfo=timezone.utc)
    result = await notion_service.update_dream_page(
        page_id="page_123",
        uploaded_at=new_time
    )

    # Verify
    assert result == mock_page
    call_args = mock_notion_client.pages.update.call_args
    properties = call_args.kwargs["properties"]

    assert properties["Date"]["date"]["start"] == "2025-02-20"
    assert properties["Wake Time"]["rich_text"][0]["text"]["content"] == "06:15"


@pytest.mark.asyncio
async def test_update_dream_page_content(notion_service, mock_notion_client):
    """Test updating dream content."""
    mock_page = {"id": "page_123", "url": "https://notion.so/page_123"}
    mock_blocks = {"results": [{"id": "block_1"}, {"id": "block_2"}]}

    mock_notion_client.pages.retrieve = AsyncMock(return_value=mock_page)
    mock_notion_client.blocks.children.list = AsyncMock(return_value=mock_blocks)
    mock_notion_client.blocks.delete = AsyncMock()
    mock_notion_client.blocks.children.append = AsyncMock()

    # Update content
    result = await notion_service.update_dream_page(
        page_id="page_123",
        dream_content="New dream content"
    )

    # Verify old blocks deleted
    assert mock_notion_client.blocks.delete.call_count == 2
    mock_notion_client.blocks.delete.assert_any_call(block_id="block_1")
    mock_notion_client.blocks.delete.assert_any_call(block_id="block_2")

    # Verify new content added
    mock_notion_client.blocks.children.append.assert_called_once()
    append_args = mock_notion_client.blocks.children.append.call_args
    assert append_args.kwargs["block_id"] == "page_123"

    children = append_args.kwargs["children"]
    assert children[0]["paragraph"]["rich_text"][0]["text"]["content"] == "New dream content"


@pytest.mark.asyncio
async def test_update_dream_page_no_changes(notion_service, mock_notion_client):
    """Test update with no changes just retrieves the page."""
    mock_page = {"id": "page_123", "url": "https://notion.so/page_123"}
    mock_notion_client.pages.retrieve = AsyncMock(return_value=mock_page)

    # Update with no parameters
    result = await notion_service.update_dream_page(page_id="page_123")

    # Should just retrieve the page
    mock_notion_client.pages.retrieve.assert_called_once_with(page_id="page_123")
    assert result == mock_page


@pytest.mark.asyncio
async def test_update_dream_page_api_error(notion_service, mock_notion_client):
    """Test update page handles API errors."""
    mock_notion_client.pages.update = AsyncMock(
        side_effect=APIResponseError(
            response=MagicMock(status_code=404),
            message="Page not found",
            code="object_not_found"
        )
    )

    # Should raise NotionAPIError
    with pytest.raises(NotionAPIError, match="Failed to update page"):
        await notion_service.update_dream_page(
            page_id="invalid_page_id",
            dream_name="New Name"
        )


@pytest.mark.asyncio
async def test_close(notion_service, mock_notion_client):
    """Test closing the Notion client."""
    await notion_service.close()
    mock_notion_client.aclose.assert_called_once()
