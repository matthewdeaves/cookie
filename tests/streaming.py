"""Test helper: make a mocked HTTP response streamable (safe_fetch reads bodies via aiter_content)."""

from unittest.mock import AsyncMock


def stream_body(response, body):
    """Set ``response.content`` to ``body`` and serve it as one streamed chunk."""
    response.content = body

    async def aiter_content():
        yield body

    response.aiter_content = aiter_content
    response.aclose = AsyncMock()
