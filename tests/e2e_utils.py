"""
Utility functions for end-to-end tests.

Provides reusable helpers for polling, waiting, and common e2e test operations.
"""
import asyncio
from typing import Callable, Any, Optional, Awaitable
from httpx import AsyncClient

# Import timeout configuration from conftest
from tests.conftest import E2E_TRANSCRIPTION_TIMEOUT, E2E_CLEANUP_TIMEOUT

DEFAULT_TRANSCRIPTION_TIMEOUT = E2E_TRANSCRIPTION_TIMEOUT
DEFAULT_CLEANUP_TIMEOUT = E2E_CLEANUP_TIMEOUT


async def poll_until_condition(
    check_fn: Callable[[], Awaitable[tuple[bool, Any]]],
    max_wait_seconds: int = 60,
    poll_interval_seconds: int = 2,
    operation_name: str = "operation",
    verbose: bool = True
) -> Any:
    """
    Poll until a condition is met or timeout occurs.

    Args:
        check_fn: Async function that returns (condition_met: bool, data: Any)
        max_wait_seconds: Maximum time to wait in seconds
        poll_interval_seconds: Time between polls in seconds
        operation_name: Name of operation for logging
        verbose: Whether to print status updates

    Returns:
        The data returned by check_fn when condition is met

    Raises:
        TimeoutError: If condition not met within max_wait_seconds
    """
    waited = 0

    if verbose:
        print(f"\nWaiting for {operation_name}...")

    while waited < max_wait_seconds:
        await asyncio.sleep(poll_interval_seconds)
        waited += poll_interval_seconds

        condition_met, data = await check_fn()

        if verbose:
            status = data.get("status", "unknown") if isinstance(data, dict) else "checking"
            print(f"  [{waited}s] {operation_name} status: {status}")

        if condition_met:
            if verbose:
                print(f"✓ {operation_name} completed")
            return data

    raise TimeoutError(f"{operation_name} did not complete within {max_wait_seconds}s")


async def wait_for_transcription(
    client: AsyncClient,
    transcription_id: str,
    max_wait: int | None = None,
    poll_interval: int = 3
) -> dict:
    """
    Wait for a transcription to complete.

    Args:
        client: Authenticated HTTP client
        transcription_id: UUID of the transcription
        max_wait: Maximum wait time in seconds (defaults to E2E_TRANSCRIPTION_TIMEOUT env var or 120s)
        poll_interval: Polling interval in seconds

    Returns:
        Completed transcription data dict

    Raises:
        TimeoutError: If transcription doesn't complete in time
        AssertionError: If transcription fails
    """
    if max_wait is None:
        max_wait = DEFAULT_TRANSCRIPTION_TIMEOUT

    async def check_transcription():
        response = await client.get(f"/api/v1/transcriptions/{transcription_id}")
        transcription = response.json()

        if transcription["status"] == "failed":
            raise AssertionError(
                f"Transcription failed: {transcription.get('error_message', 'Unknown error')}"
            )

        is_complete = transcription["status"] == "completed"
        return is_complete, transcription

    return await poll_until_condition(
        check_fn=check_transcription,
        max_wait_seconds=max_wait,
        poll_interval_seconds=poll_interval,
        operation_name="transcription"
    )


async def wait_for_cleanup(
    client: AsyncClient,
    cleanup_id: str,
    max_wait: int | None = None,
    poll_interval: int = 3
) -> dict:
    """
    Wait for a cleanup to complete.

    Args:
        client: Authenticated HTTP client
        cleanup_id: UUID of the cleaned entry
        max_wait: Maximum wait time in seconds (defaults to E2E_CLEANUP_TIMEOUT env var or 120s)
        poll_interval: Polling interval in seconds

    Returns:
        Completed cleanup data dict

    Raises:
        TimeoutError: If cleanup doesn't complete in time
        AssertionError: If cleanup fails
    """
    if max_wait is None:
        max_wait = DEFAULT_CLEANUP_TIMEOUT

    async def check_cleanup():
        response = await client.get(f"/api/v1/cleaned-entries/{cleanup_id}")
        cleaned_entry = response.json()

        if cleaned_entry["status"] == "failed":
            raise AssertionError(
                f"Cleanup failed: {cleaned_entry.get('error_message', 'Unknown error')}"
            )

        is_complete = cleaned_entry["status"] == "completed"
        return is_complete, cleaned_entry

    return await poll_until_condition(
        check_fn=check_cleanup,
        max_wait_seconds=max_wait,
        poll_interval_seconds=poll_interval,
        operation_name="cleanup"
    )
