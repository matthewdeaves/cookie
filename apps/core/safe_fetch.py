"""SSRF-safe HTTP fetch: the single owner of the redirect/validation/pinning loop.

Interface (the test surface):
    ``await safe_fetch(url, session_factory=..., impersonate=..., timeout=...)``

What this module guarantees, for every caller:
    * the first hop is validated and DNS-pinned unless the caller already did that and passes
      ``curl_resolve`` (a ``ResolvedURL.curl_resolve`` list from ``validate_url``);
    * redirects are never followed by the HTTP client; each ``Location`` is validated against
      the SSRF blocklist and its resolved IP is pinned for the next request;
    * the hop count is capped (``MAX_REDIRECT_HOPS``) and, optionally, a 200 body is capped
      (``max_size``: Content-Length first, then the real body).

Callers keep their own rules: browser-profile retries, status-code mapping (404/429/...),
image sniffing and how to report an error. They receive the final response (which may be a
redirect with no ``Location``) or one of the ``ValueError`` subclasses below. The HTTP client
is injected (``session_factory``, e.g. curl_cffi's ``AsyncSession``) so this module has no
network dependency of its own and tests can drive it with a fake.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, NamedTuple

from apps.core.validators import (
    MAX_REDIRECT_HOPS,
    check_response_size,
    validate_redirect_url,
    validate_url,
)

REDIRECT_STATUSES = (301, 302, 303, 307, 308)


class Fetched(NamedTuple):
    """The final response and the URL it was actually fetched from (after any redirects)."""

    response: Any
    url: str


class RedirectLimitExceeded(ValueError):
    """The redirect chain was longer than ``MAX_REDIRECT_HOPS``."""


class ResponseTooLarge(ValueError):
    """A 200 body exceeded ``max_size`` (declared by Content-Length or actually received)."""


async def _read_body(response: Any, max_size: int) -> bool:
    """Stream the body into ``response.content``, stopping past ``max_size``.

    Returns True when the body exceeded the cap (the download is aborted and ``content`` holds
    what was read so far).
    """
    chunks: list[bytes] = []
    received = 0
    over = False
    async for chunk in response.aiter_content():
        received += len(chunk)
        chunks.append(chunk)
        if received > max_size:
            over = True
            break
    response.content = b"".join(chunks)
    if over:
        quit_now = getattr(response, "quit_now", None)
        if quit_now is not None:
            quit_now.set()
    try:
        await response.aclose()
    except Exception:  # best-effort teardown of an aborted download
        pass
    return over


async def safe_fetch(
    url: str,
    *,
    session_factory: Callable[..., Any],
    impersonate: Any,
    timeout: float,
    curl_resolve: list[str] | None = None,
    max_size: int | None = None,
    hard_timeout: float | None = None,
) -> Fetched:
    """GET ``url`` following redirects manually with SSRF validation on every hop.

    Args:
        session_factory: ``AsyncSession``-compatible callable taking ``impersonate`` and
            ``curl_options`` and returning an async context manager with ``.get()``.
        curl_resolve: pinned DNS for the first hop if the caller already validated ``url``;
            when None the first hop is validated here (raises ValueError if unsafe).
        max_size: cap for a 200 response body; raises ``ResponseTooLarge``.
        hard_timeout: overall per-request ceiling enforced with ``asyncio.wait_for``.

    Returns ``Fetched(response, url)``: the first non-redirect response (or a redirect with no
    Location) and the URL it came from.
    Raises ValueError (blocked/unresolvable URL), ``RedirectLimitExceeded`` or
    ``ResponseTooLarge``; network errors from the client propagate unchanged.
    """
    from curl_cffi import CurlOpt

    current_url = url
    current_resolve = curl_resolve if curl_resolve is not None else validate_url(url).curl_resolve
    stream = {"stream": True} if max_size is not None else {}

    for _ in range(MAX_REDIRECT_HOPS):
        curl_opts = {CurlOpt.RESOLVE: current_resolve} if current_resolve else {}
        async with session_factory(impersonate=impersonate, curl_options=curl_opts) as session:
            request = session.get(current_url, timeout=timeout, allow_redirects=False, **stream)
            response = await (asyncio.wait_for(request, timeout=hard_timeout) if hard_timeout else request)
            over = False
            if stream and response.status_code == 200 and not check_response_size(response, max_size):
                raise ResponseTooLarge(f"Response too large (Content-Length > {max_size})")
            if stream and response.status_code not in REDIRECT_STATUSES:
                body = _read_body(response, max_size)
                over = await (asyncio.wait_for(body, timeout=hard_timeout) if hard_timeout else body)

        if response.status_code in REDIRECT_STATUSES:
            location = response.headers.get("location")
            if not location:
                return Fetched(response, current_url)
            current_resolve = validate_redirect_url(location).curl_resolve
            current_url = location
            continue

        if response.status_code == 200 and max_size is not None:
            if over:
                raise ResponseTooLarge(f"Response too large (limit: {max_size} bytes)")
        return Fetched(response, current_url)

    raise RedirectLimitExceeded(f"Too many redirects (>{MAX_REDIRECT_HOPS}) for {url}")
