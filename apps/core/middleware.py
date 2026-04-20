import ipaddress
import re
import uuid

from django.conf import settings
from django.http import JsonResponse


def get_client_ip(request):
    """Extract the real client IP from X-Forwarded-For for django-ratelimit.

    X-Forwarded-For may contain multiple IPs: "client, proxy1, proxy2".
    We take the leftmost entry (the original client), validate it as a
    real IP address, and return it.  Falls back to REMOTE_ADDR if the
    header is missing or every entry is malformed.

    Used via RATELIMIT_IP_META_KEY = "apps.core.middleware.get_client_ip"
    """
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        # Take the leftmost (client) IP, strip whitespace
        candidate = forwarded_for.split(",")[0].strip()
        try:
            ipaddress.ip_address(candidate)
            return candidate
        except ValueError:
            pass
    return request.META.get("REMOTE_ADDR", "127.0.0.1")


class RequestIDMiddleware:
    """Attach a unique request_id to each request for log correlation."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = str(uuid.uuid4())[:8]
        response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        return response


class DeviceDetectionMiddleware:
    """Middleware to detect legacy browsers that can't run modern React.

    Sets request.is_legacy_device = True for browsers that need the legacy frontend:
    - iOS < 11 (Safari lacks ES6 module support)
    - Internet Explorer (all versions)
    - Edge Legacy (non-Chromium, pre-2020)
    - Chrome < 60
    - Firefox < 55

    Note: Actual redirects are handled by Nginx for performance (see nginx/nginx.conf).
    This middleware provides the detection flag for use in views/templates if needed.
    """

    # Pattern to match iOS version from user agent
    IOS_PATTERN = re.compile(r"(?:iPhone|iPad|iPod).*OS (\d+)_")

    # Pattern to match Chrome version
    CHROME_PATTERN = re.compile(r"Chrome/(\d+)\.")

    # Pattern to match Firefox version
    FIREFOX_PATTERN = re.compile(r"Firefox/(\d+)\.")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.is_legacy_device = self._is_legacy_device(request)
        return self.get_response(request)

    def _is_legacy_device(self, request):
        """Check if the request is from a browser that can't run modern React."""
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        if not user_agent:
            return False

        detectors = [
            self._is_legacy_ios,
            self._is_internet_explorer,
            self._is_edge_legacy,
            self._is_old_chrome,
            self._is_old_firefox,
        ]
        return any(detect(user_agent) for detect in detectors)

    def _is_legacy_ios(self, ua):
        """iOS < 11 (Safari lacks ES6 module support)."""
        match = self.IOS_PATTERN.search(ua)
        return match is not None and int(match.group(1)) < 11

    def _is_internet_explorer(self, ua):
        """Internet Explorer (all versions)."""
        return "MSIE " in ua or "Trident/" in ua

    def _is_edge_legacy(self, ua):
        """Edge Legacy (non-Chromium, pre-2020)."""
        return "Edge/" in ua and "Edg/" not in ua

    def _is_old_chrome(self, ua):
        """Chrome < 60 (excluding Edge and Opera)."""
        if "Chrome/" not in ua or "Edg" in ua or "OPR/" in ua:
            return False
        match = self.CHROME_PATTERN.search(ua)
        return match is not None and int(match.group(1)) < 60

    def _is_old_firefox(self, ua):
        """Firefox < 55."""
        match = self.FIREFOX_PATTERN.search(ua)
        return match is not None and int(match.group(1)) < 55


def _ninja_path_to_regex(path: str) -> re.Pattern:
    """Convert a Ninja URL path (with `{param}` / `{param:int}` placeholders)
    to a compiled regex that matches a single URL, with an optional trailing
    slash. A `{param}` spans exactly one path segment (no slashes)."""
    pattern = re.sub(r"\{[^/}]+\}", r"[^/]+", path.rstrip("/"))
    return re.compile(rf"^{pattern}/?$")


_home_only_patterns_cache: tuple[re.Pattern, ...] | None = None


def _home_only_patterns() -> tuple[re.Pattern, ...]:
    """Introspect the Ninja API once to compile regexes for every path
    whose registered methods ALL use `HomeOnlyAuth`. A path that mixes
    `HomeOnlyAuth` methods with `SessionAuth` methods (e.g. `/api/ai/quotas`
    has GET=SessionAuth + PUT=HomeOnlyAuth) is NOT included here — those
    paths must remain reachable in passkey mode for the non-gated methods.
    Lazy-imported to avoid a circular import at module load (urls → ninja
    routers → auth classes → middleware)."""
    global _home_only_patterns_cache
    if _home_only_patterns_cache is not None:
        return _home_only_patterns_cache

    from apps.core.auth import HomeOnlyAuth
    from cookie.urls import api

    paths: set[str] = set()
    for prefix, router in api._routers:
        for path, path_op in router.path_operations.items():
            if not path_op.operations:
                continue
            all_home_only = all(
                any(isinstance(a, HomeOnlyAuth) for a in (op.auth_callbacks or [])) for op in path_op.operations
            )
            if all_home_only:
                paths.add(f"/api{prefix}{path}")

    _home_only_patterns_cache = tuple(_ninja_path_to_regex(p) for p in paths)
    return _home_only_patterns_cache


class HomeOnlyRouteGateMiddleware:
    """Short-circuit every method on HomeOnlyAuth-gated routes to 404 in
    non-home auth modes, above Django's URL dispatcher.

    Without this, HEAD/OPTIONS (and other unregistered methods) on gated
    routes fall through to Django's 405 handler, which emits an `Allow:`
    header listing the real method set — leaking route existence to
    unauthenticated probes. The v1.42.0 security posture promises that
    gated routes are "indistinguishable from never-existed paths"; this
    middleware upholds that promise for every verb, not just those with
    a registered Ninja handler.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.AUTH_MODE != "home":
            path = request.path
            for pattern in _home_only_patterns():
                if pattern.match(path):
                    return JsonResponse({"detail": "Not found"}, status=404)
        return self.get_response(request)


class MethodNotAllowedToNotFoundMiddleware:
    """Rewrite every HTTP 405 response to a JSON 404.

    Rationale: a 405 "Method Not Allowed" response tells a probe that the
    URL exists but doesn't accept this method. For POST-only endpoints
    like `/api/auth/logout/` and `/api/auth/device/authorize/`, an
    unauthenticated `GET` would otherwise return 405 — contradicting the
    v1.42.0 "gated paths are indistinguishable from never-existed paths"
    invariant that `HomeOnlyRouteGateMiddleware` established for
    HomeOnlyAuth routes (pentest round 6 / F-5).

    The rewrite is global rather than per-endpoint because:
    - Cookie's clients (React frontend, legacy ES5 frontend) never rely
      on 405 for control flow — they only issue documented methods.
    - A global rule removes the possibility of forgetting to gate a new
      POST-only endpoint.
    - The existing `Allow:` header that Django attaches to 405 responses
      also leaks the method set; collapsing to 404 drops it.

    Nginx-generated 405s (none occur in the current config, but a future
    location block could introduce one) are separately rewritten to 404
    via `error_page 405 =404 @not_found;` in `nginx/nginx.prod.conf`.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 405:
            return JsonResponse({"detail": "Not found"}, status=404)
        return response
