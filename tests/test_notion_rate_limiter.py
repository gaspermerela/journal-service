"""
Unit tests for Notion rate limiter.

Tests token bucket rate limiting algorithm.
"""

import pytest
import asyncio
import time
from app.services.notion_rate_limiter import NotionRateLimiter


@pytest.mark.asyncio
async def test_basic_rate_limiting():
    """Test basic rate limiting allows requests within limit."""
    limiter = NotionRateLimiter(requests_per_second=3, period=1)

    # Should allow 3 requests immediately
    start = time.monotonic()
    for _ in range(3):
        async with limiter:
            pass
    elapsed = time.monotonic() - start

    # Should complete almost instantly (no rate limiting)
    assert elapsed < 0.1


@pytest.mark.asyncio
async def test_rate_limiting_enforced():
    """Test rate limiting enforces delay after exceeding limit."""
    limiter = NotionRateLimiter(requests_per_second=3, period=1)

    # Consume all 3 tokens
    for _ in range(3):
        async with limiter:
            pass

    # 4th request should be delayed
    start = time.monotonic()
    async with limiter:
        pass
    elapsed = time.monotonic() - start

    # Should wait ~0.33 seconds (1/3 second for 3 req/sec)
    assert 0.2 < elapsed < 0.5


@pytest.mark.asyncio
async def test_token_refill():
    """Test tokens refill over time."""
    limiter = NotionRateLimiter(requests_per_second=2, period=1)

    # Consume 2 tokens
    for _ in range(2):
        async with limiter:
            pass

    # Wait for token refill (0.5 seconds = 1 token)
    await asyncio.sleep(0.6)

    # Should have 1 token available now (no delay)
    start = time.monotonic()
    async with limiter:
        pass
    elapsed = time.monotonic() - start

    assert elapsed < 0.1


@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test rate limiter works with concurrent requests."""
    limiter = NotionRateLimiter(requests_per_second=5, period=1)

    async def make_request():
        async with limiter:
            await asyncio.sleep(0.01)  # Simulate API call

    # Launch 10 concurrent requests
    start = time.monotonic()
    await asyncio.gather(*[make_request() for _ in range(10)])
    elapsed = time.monotonic() - start

    # First 5 should be immediate, next 5 should wait ~1 second
    # Total time should be around 1-1.5 seconds
    assert 0.8 < elapsed < 2.0


@pytest.mark.asyncio
async def test_acquire_method():
    """Test acquire method directly."""
    limiter = NotionRateLimiter(requests_per_second=2, period=1)

    # Acquire 2 tokens
    await limiter.acquire()
    await limiter.acquire()

    # 3rd acquire should block
    start = time.monotonic()
    await limiter.acquire()
    elapsed = time.monotonic() - start

    # Should wait ~0.5 seconds
    assert 0.3 < elapsed < 0.8


@pytest.mark.asyncio
async def test_default_config():
    """Test rate limiter uses config defaults."""
    from app.config import settings

    limiter = NotionRateLimiter()

    assert limiter.max_requests == settings.NOTION_RATE_LIMIT_REQUESTS
    assert limiter.period == settings.NOTION_RATE_LIMIT_PERIOD


@pytest.mark.asyncio
async def test_custom_config():
    """Test rate limiter accepts custom config."""
    limiter = NotionRateLimiter(requests_per_second=10, period=2)

    assert limiter.max_requests == 10
    assert limiter.period == 2


@pytest.mark.asyncio
async def test_tokens_dont_exceed_max():
    """Test tokens don't exceed bucket capacity."""
    limiter = NotionRateLimiter(requests_per_second=3, period=1)

    # Wait for tokens to fully refill
    await asyncio.sleep(2)

    # Force refill
    await limiter._refill_tokens()

    # Tokens should be capped at max_requests
    assert limiter.tokens <= limiter.max_requests


@pytest.mark.asyncio
async def test_get_rate_limiter_singleton():
    """Test get_rate_limiter returns singleton instance."""
    from app.services.notion_rate_limiter import get_rate_limiter

    limiter1 = get_rate_limiter()
    limiter2 = get_rate_limiter()

    # Should be the same instance
    assert limiter1 is limiter2
