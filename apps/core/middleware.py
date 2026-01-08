import re


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
    IOS_PATTERN = re.compile(r'(?:iPhone|iPad|iPod).*OS (\d+)_')

    # Pattern to match Chrome version
    CHROME_PATTERN = re.compile(r'Chrome/(\d+)\.')

    # Pattern to match Firefox version
    FIREFOX_PATTERN = re.compile(r'Firefox/(\d+)\.')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.is_legacy_device = self._is_legacy_device(request)
        return self.get_response(request)

    def _is_legacy_device(self, request):
        """Check if the request is from a browser that can't run modern React."""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if not user_agent:
            return False

        # iOS < 11
        match = self.IOS_PATTERN.search(user_agent)
        if match:
            return int(match.group(1)) < 11

        # Internet Explorer
        if 'MSIE ' in user_agent or 'Trident/' in user_agent:
            return True

        # Edge Legacy (non-Chromium)
        if 'Edge/' in user_agent and 'Edg/' not in user_agent:
            return True

        # Chrome < 60
        if 'Chrome/' in user_agent and 'Edg' not in user_agent and 'OPR/' not in user_agent:
            match = self.CHROME_PATTERN.search(user_agent)
            if match and int(match.group(1)) < 60:
                return True

        # Firefox < 55
        match = self.FIREFOX_PATTERN.search(user_agent)
        if match and int(match.group(1)) < 55:
            return True

        return False
