"""Tests for core middleware functions."""

import json

import pytest
from django.http import HttpResponse, HttpResponseNotAllowed
from django.test import RequestFactory

from apps.core.middleware import (
    MethodNotAllowedToNotFoundMiddleware,
    get_client_ip,
)


class TestGetClientIp:
    """Test IP extraction from X-Forwarded-For for rate limiting."""

    def _make_request(self, **meta):
        rf = RequestFactory()
        request = rf.get("/")
        request.META.update(meta)
        return request

    def test_single_ip(self):
        request = self._make_request(HTTP_X_FORWARDED_FOR="192.168.1.1")
        assert get_client_ip(request) == "192.168.1.1"

    def test_multi_proxy_chain(self):
        request = self._make_request(HTTP_X_FORWARDED_FOR="81.141.119.30, 172.18.0.1, 172.18.0.2")
        assert get_client_ip(request) == "81.141.119.30"

    def test_ipv6(self):
        request = self._make_request(HTTP_X_FORWARDED_FOR="2a09:bac3:3759:278::3f:dd, 172.18.0.1")
        assert get_client_ip(request) == "2a09:bac3:3759:278::3f:dd"

    def test_no_forwarded_for_uses_remote_addr(self):
        request = self._make_request(REMOTE_ADDR="10.0.0.1")
        assert get_client_ip(request) == "10.0.0.1"

    def test_malformed_ip_falls_back(self):
        request = self._make_request(HTTP_X_FORWARDED_FOR="not-an-ip, 172.18.0.1", REMOTE_ADDR="172.18.0.2")
        assert get_client_ip(request) == "172.18.0.2"

    def test_empty_forwarded_for(self):
        request = self._make_request(HTTP_X_FORWARDED_FOR="", REMOTE_ADDR="127.0.0.1")
        assert get_client_ip(request) == "127.0.0.1"

    def test_no_headers_defaults(self):
        rf = RequestFactory()
        request = rf.get("/")
        ip = get_client_ip(request)
        assert ip  # Should return something, not crash


class TestMethodNotAllowedToNotFoundMiddleware:
    """Pentest round 6 / F-5: every 405 must become a 404 so POST-only
    endpoints don't leak their existence on GET probes."""

    def _make_middleware(self, downstream_response):
        rf = RequestFactory()
        request = rf.get("/does-not-matter")

        def get_response(_request):
            return downstream_response

        middleware = MethodNotAllowedToNotFoundMiddleware(get_response)
        return middleware(request)

    def test_405_becomes_404_json(self):
        # Django's HttpResponseNotAllowed is the canonical producer of 405.
        downstream = HttpResponseNotAllowed(["POST"])
        assert downstream.status_code == 405

        response = self._make_middleware(downstream)

        assert response.status_code == 404
        assert response["Content-Type"].startswith("application/json")
        body = json.loads(response.content)
        assert body == {"detail": "Not found"}

    def test_405_rewrite_drops_allow_header(self):
        """Django attaches `Allow:` to 405 — that header itself enumerates
        the method set, so the rewritten 404 must NOT carry it through."""
        downstream = HttpResponseNotAllowed(["POST", "PUT"])
        assert downstream["Allow"]  # sanity — present before middleware

        response = self._make_middleware(downstream)

        assert response.status_code == 404
        assert "Allow" not in response  # dropped by the JsonResponse swap

    def test_non_405_passes_through_unchanged(self):
        """The middleware must not touch any other status code."""
        downstream = HttpResponse("ok", status=200)

        response = self._make_middleware(downstream)

        assert response is downstream  # same object, nothing rewrapped
        assert response.status_code == 200

    @pytest.mark.parametrize("status", [400, 401, 403, 404, 500, 502])
    def test_other_4xx_5xx_pass_through(self, status):
        downstream = HttpResponse(f"status {status}", status=status)
        response = self._make_middleware(downstream)
        assert response.status_code == status
        assert response is downstream
