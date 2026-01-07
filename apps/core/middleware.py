# Device detection middleware will be added in Session B


class DeviceDetectionMiddleware:
    """Placeholder middleware for device detection."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.is_legacy_device = False
        return self.get_response(request)
