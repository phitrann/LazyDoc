"""In-flight request deduplication.

When multiple concurrent requests are made for the same repository,
deduplicate to make only a single GitHub API call and share the result.
"""

from __future__ import annotations

import asyncio
from typing import TypeVar, Callable, Any

T = TypeVar("T")


class RequestDeduplicator:
    """Deduplicate concurrent requests for the same key."""

    def __init__(self) -> None:
        self._in_flight: dict[str, asyncio.Event] = {}
        self._results: dict[str, Any] = {}

    async def dedupe(self, key: str, fn: Callable[[], Any]) -> Any:
        """
        Execute fn() once per key, returning the same result to all concurrent callers.
        
        Args:
            key: Unique key for this request (e.g., "owner/repo")
            fn: Async callable to execute
            
        Returns:
            Result from fn() shared across all callers with same key
        """
        if key in self._in_flight:
            await self._in_flight[key].wait()
            return self._results.get(key)

        event = asyncio.Event()
        self._in_flight[key] = event
        try:
            result = await fn()
            self._results[key] = result
            return result
        finally:
            event.set()
            self._in_flight.pop(key, None)

    def clear(self) -> None:
        """Clear all cached results (but not in-flight requests)."""
        self._results.clear()


_dedupe = RequestDeduplicator()


def get_dedupe() -> RequestDeduplicator:
    """Get the global deduplicator instance."""
    return _dedupe
