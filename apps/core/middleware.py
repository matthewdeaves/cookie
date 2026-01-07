import re


class DeviceDetectionMiddleware:
    """Middleware to detect legacy iOS devices (iOS 9 and earlier)."""

    # Pattern to match iOS version from user agent
    # Examples:
    # - "Mozilla/5.0 (iPad; CPU OS 9_3_5 like Mac OS X)"
    # - "Mozilla/5.0 (iPhone; CPU iPhone OS 9_0 like Mac OS X)"
    IOS_PATTERN = re.compile(r'(?:iPhone|iPad|iPod).*OS (\d+)_')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.is_legacy_device = self._is_legacy_device(request)
        return self.get_response(request)

    def _is_legacy_device(self, request):
        """Check if the request is from a legacy iOS device (iOS 9 or earlier)."""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if not user_agent:
            return False

        match = self.IOS_PATTERN.search(user_agent)
        if match:
            ios_version = int(match.group(1))
            return ios_version <= 9

        return False
