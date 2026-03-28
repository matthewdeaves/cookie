import ipaddress
import re
import uuid


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

        # iOS < 11
        match = self.IOS_PATTERN.search(user_agent)
        if match:
            return int(match.group(1)) < 11

        # Internet Explorer
        if "MSIE " in user_agent or "Trident/" in user_agent:
            return True

        # Edge Legacy (non-Chromium)
        if "Edge/" in user_agent and "Edg/" not in user_agent:
            return True

        # Chrome < 60
        if "Chrome/" in user_agent and "Edg" not in user_agent and "OPR/" not in user_agent:
            match = self.CHROME_PATTERN.search(user_agent)
            if match and int(match.group(1)) < 60:
                return True

        # Firefox < 55
        match = self.FIREFOX_PATTERN.search(user_agent)
        if match and int(match.group(1)) < 55:
            return True

        return False
