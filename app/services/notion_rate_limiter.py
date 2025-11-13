"""
Rate limiter for Notion API requests.

Implements token bucket algorithm to respect Notion's rate limits (3 req/sec).
Thread-safe for use in async contexts.
"""

import asyncio
import time
from typing import Optional
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("notion_rate_limiter")


class NotionRateLimiter:
    """
    Token bucket rate limiter for Notion API.

    Ensures we don't exceed Notion's rate limit of 3 requests per second.
    Thread-safe implementation using asyncio locks.

    Usage:
        limiter = NotionRateLimiter()
        async with limiter:
            # Make Notion API call
            response = await notion_client.pages.create(...)
    """

    def __init__(
        self,
        requests_per_second: Optional[int] = None,
        period: Optional[int] = None
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Max requests per period (defaults to config)
            period: Time period in seconds (defaults to config)
        """
        self.max_requests = requests_per_second or settings.NOTION_RATE_LIMIT_REQUESTS
        self.period = period or settings.NOTION_RATE_LIMIT_PERIOD

        # Token bucket state
        self.tokens = float(self.max_requests)
        self.last_refill = time.monotonic()

        # Async lock for thread safety
        self._lock = asyncio.Lock()

        logger.info(
            f"Initialized rate limiter",
            max_requests=self.max_requests,
            period=self.period
        )

    async def _refill_tokens(self) -> None:
        """
        Refill tokens based on elapsed time.

        Tokens are added at a constant rate: max_requests / period.
        Tokens are capped at max_requests (bucket capacity).
        """
        now = time.monotonic()
        elapsed = now - self.last_refill

        # Calculate tokens to add based on elapsed time
        tokens_to_add = elapsed * (self.max_requests / self.period)

        if tokens_to_add > 0:
            self.tokens = min(self.max_requests, self.tokens + tokens_to_add)
            self.last_refill = now

            logger.debug(
                f"Refilled tokens",
                tokens=self.tokens,
                elapsed=elapsed
            )

    async def acquire(self) -> None:
        """
        Acquire permission to make a request.

        Blocks until a token is available. This implements the rate limiting.
        """
        async with self._lock:
            while True:
                await self._refill_tokens()

                if self.tokens >= 1:
                    # Token available - consume it and proceed
                    self.tokens -= 1
                    logger.debug(
                        f"Token acquired",
                        remaining_tokens=self.tokens
                    )
                    return
                else:
                    # No tokens - calculate wait time
                    wait_time = (1 - self.tokens) * (self.period / self.max_requests)
                    logger.debug(
                        f"Rate limit reached, waiting",
                        wait_time=wait_time
                    )
                    await asyncio.sleep(wait_time)

    async def __aenter__(self):
        """Context manager entry - acquire token."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - nothing to cleanup."""
        pass


# Global rate limiter instance
_rate_limiter: Optional[NotionRateLimiter] = None


def get_rate_limiter() -> NotionRateLimiter:
    """
    Get or create global rate limiter instance.

    Returns:
        Shared NotionRateLimiter instance

    Example:
        limiter = get_rate_limiter()
        async with limiter:
            await notion_client.pages.create(...)
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = NotionRateLimiter()
    return _rate_limiter
