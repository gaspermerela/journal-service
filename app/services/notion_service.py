"""
Notion API integration service.

Handles communication with Notion API for creating and updating dream journal pages.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from notion_client import AsyncClient
from notion_client.errors import APIResponseError

from app.config import settings
from app.utils.logger import get_logger
from app.services.notion_rate_limiter import get_rate_limiter

logger = get_logger("notion_service")


class NotionError(Exception):
    """Base exception for Notion-related errors."""
    pass


class NotionValidationError(NotionError):
    """Raised when database validation fails."""
    pass


class NotionAPIError(NotionError):
    """Raised when Notion API returns an error."""
    pass


class NotionService:
    """
    Service for interacting with Notion API.

    Handles:
    - Database validation
    - Creating dream pages
    - Updating dream pages
    - Rate limiting
    - Error handling with retries
    """

    def __init__(self, api_key: str):
        """
        Initialize Notion service.

        Args:
            api_key: Decrypted Notion API key
        """
        self.client = AsyncClient(auth=api_key)
        self.rate_limiter = get_rate_limiter()
        logger.info("Initialized Notion service")

    async def validate_database(self, database_id: str) -> Dict[str, Any]:
        """
        Validate database exists and has required properties.

        Checks for:
        - Database accessibility
        - Required properties: Name (title), Date (date), Wake Time (rich_text)

        Args:
            database_id: Notion database ID to validate

        Returns:
            Database metadata including properties

        Raises:
            NotionValidationError: If database is invalid or missing properties
            NotionAPIError: If API call fails

        Example:
            >>> db_info = await notion_service.validate_database("abc123")
            >>> print(db_info["title"][0]["plain_text"])
            'Dream Journal'
        """
        try:
            # Step 1: Retrieve database to get data_source_id
            async with self.rate_limiter:
                database = await self.client.databases.retrieve(database_id=database_id)

            logger.info(
                "Retrieved database",
                database_id=database_id,
                title=database.get("title", [{}])[0].get("plain_text", "Unknown")
            )

            # Step 2: Get properties from data source
            # Note: databases.retrieve() does NOT return properties field
            # We must use data_sources.retrieve() to get the schema
            data_sources = database.get("data_sources", [])
            if not data_sources:
                raise NotionValidationError(
                    "Database has no data sources. This database may not be accessible."
                )

            data_source_id = data_sources[0]["id"]
            logger.info(
                "Retrieving data source for properties",
                data_source_id=data_source_id
            )

            async with self.rate_limiter:
                data_source = await self.client.data_sources.retrieve(
                    data_source_id=data_source_id
                )

            # Check required properties from data source
            properties = data_source.get("properties", {})
            required_props = {
                "Name": "title",
                "Date": "date",
                "Wake Time": "rich_text"
            }

            missing = []
            wrong_type = []

            for prop_name, expected_type in required_props.items():
                if prop_name not in properties:
                    missing.append(prop_name)
                elif properties[prop_name].get("type") != expected_type:
                    wrong_type.append(
                        f"{prop_name} (expected {expected_type}, got {properties[prop_name].get('type')})"
                    )

            if missing or wrong_type:
                error_msg = "Database validation failed: "
                if missing:
                    error_msg += f"missing properties: {', '.join(missing)}. "
                if wrong_type:
                    error_msg += f"wrong property types: {', '.join(wrong_type)}."

                logger.error(
                    "Database validation failed",
                    database_id=database_id,
                    missing=missing,
                    wrong_type=wrong_type
                )
                raise NotionValidationError(error_msg)

            logger.info(
                "Database validation successful",
                database_id=database_id,
                properties_count=len(properties)
            )

            # Return database metadata with properties from data source
            return {
                **database,
                "properties": properties
            }

        except APIResponseError as e:
            logger.error(
                "Notion API error during validation",
                database_id=database_id,
                status=e.status,
                code=e.code,
                message=str(e)
            )
            raise NotionAPIError(f"Failed to validate database: {str(e)}") from e
        except NotionValidationError:
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during validation",
                database_id=database_id,
                error=str(e),
                exc_info=True
            )
            raise NotionAPIError(f"Unexpected error: {str(e)}") from e

    async def create_dream_page(
        self,
        database_id: str,
        dream_content: str,
        uploaded_at: datetime,
        dream_name: str = "Dream"
    ) -> Dict[str, Any]:
        """
        Create a new dream page in Notion database.

        For Phase 5, creates simple properties:
        - Name: "Dream" (hardcoded title)
        - Date: Upload date (from uploaded_at)
        - Wake Time: HH:MM from uploaded_at timestamp
        - Page content: Dream text

        Args:
            database_id: Target Notion database ID
            dream_content: Dream text to store in page body
            uploaded_at: Upload timestamp (used for Date and Wake Time)
            dream_name: Title for the dream (default: "Dream")

        Returns:
            Created page object from Notion API

        Raises:
            NotionAPIError: If page creation fails

        Example:
            >>> page = await notion_service.create_dream_page(
            ...     database_id="abc123",
            ...     dream_content="I was flying over mountains...",
            ...     uploaded_at=datetime(2025, 1, 15, 4, 30, tzinfo=timezone.utc)
            ... )
            >>> print(page["url"])
            'https://notion.so/...'
        """
        try:
            # Format wake time as HH:MM
            wake_time = uploaded_at.strftime("%H:%M")

            # Format date as YYYY-MM-DD
            date_str = uploaded_at.strftime("%Y-%m-%d")

            # Build page properties
            properties = {
                "Name": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": dream_name}
                        }
                    ]
                },
                "Date": {
                    "date": {"start": date_str}
                },
                "Wake Time": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": wake_time}
                        }
                    ]
                }
            }

            # Build page content (dream text in page body)
            children = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": dream_content}
                            }
                        ]
                    }
                }
            ]

            logger.info(
                "Creating dream page",
                database_id=database_id,
                dream_name=dream_name,
                date=date_str,
                wake_time=wake_time,
                content_length=len(dream_content)
            )

            async with self.rate_limiter:
                page = await self.client.pages.create(
                    parent={"database_id": database_id},
                    properties=properties,
                    children=children
                )

            logger.info(
                "Dream page created",
                page_id=page["id"],
                url=page["url"]
            )
            return page

        except APIResponseError as e:
            logger.error(
                "Notion API error creating page",
                database_id=database_id,
                status=e.status,
                code=e.code,
                message=str(e)
            )
            raise NotionAPIError(f"Failed to create page: {str(e)}") from e
        except Exception as e:
            logger.error(
                "Unexpected error creating page",
                database_id=database_id,
                error=str(e),
                exc_info=True
            )
            raise NotionAPIError(f"Unexpected error: {str(e)}") from e

    async def update_dream_page(
        self,
        page_id: str,
        dream_content: Optional[str] = None,
        uploaded_at: Optional[datetime] = None,
        dream_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing dream page.

        Only updates provided fields. Useful for syncing changes.

        Args:
            page_id: Notion page ID to update
            dream_content: New dream text (replaces page content if provided)
            uploaded_at: New timestamp (updates Date and Wake Time if provided)
            dream_name: New title (updates Name if provided)

        Returns:
            Updated page object from Notion API

        Raises:
            NotionAPIError: If update fails

        Example:
            >>> page = await notion_service.update_dream_page(
            ...     page_id="page_abc123",
            ...     dream_name="Lucid Flight Dream"
            ... )
        """
        try:
            properties = {}

            # Update name if provided
            if dream_name is not None:
                properties["Name"] = {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": dream_name}
                        }
                    ]
                }

            # Update date/time if provided
            if uploaded_at is not None:
                wake_time = uploaded_at.strftime("%H:%M")
                date_str = uploaded_at.strftime("%Y-%m-%d")

                properties["Date"] = {
                    "date": {"start": date_str}
                }
                properties["Wake Time"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": wake_time}
                        }
                    ]
                }

            logger.info(
                "Updating dream page",
                page_id=page_id,
                has_content=dream_content is not None,
                has_timestamp=uploaded_at is not None,
                has_name=dream_name is not None
            )

            # Update properties if any
            if properties:
                async with self.rate_limiter:
                    page = await self.client.pages.update(
                        page_id=page_id,
                        properties=properties
                    )
            else:
                # Just retrieve the page if no properties to update
                async with self.rate_limiter:
                    page = await self.client.pages.retrieve(page_id=page_id)

            # Update content if provided
            if dream_content is not None:
                # Delete existing blocks
                async with self.rate_limiter:
                    blocks = await self.client.blocks.children.list(block_id=page_id)

                for block in blocks.get("results", []):
                    async with self.rate_limiter:
                        await self.client.blocks.delete(block_id=block["id"])

                # Add new content
                children = [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": dream_content}
                                }
                            ]
                        }
                    }
                ]

                async with self.rate_limiter:
                    await self.client.blocks.children.append(
                        block_id=page_id,
                        children=children
                    )

            logger.info(
                "Dream page updated",
                page_id=page_id
            )
            return page

        except APIResponseError as e:
            logger.error(
                "Notion API error updating page",
                page_id=page_id,
                status=e.status,
                code=e.code,
                message=str(e)
            )
            raise NotionAPIError(f"Failed to update page: {str(e)}") from e
        except Exception as e:
            logger.error(
                "Unexpected error updating page",
                page_id=page_id,
                error=str(e),
                exc_info=True
            )
            raise NotionAPIError(f"Unexpected error: {str(e)}") from e

    async def close(self):
        """Close the Notion client session."""
        await self.client.aclose()
        logger.info("Closed Notion client")
