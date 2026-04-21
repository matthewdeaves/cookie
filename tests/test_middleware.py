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
    """Test IP extraction for rate limiting.

    Priority: CF-Connecting-IP > rightmost X-Forwarded-For > REMOTE_ADDR.
    CF-Connecting-IP is set authoritatively by Cloudflare; clients cannot
    inject fake values.  The leftmost X-Forwarded-For entry is attacker-
    controlled and must NOT be used.
    """

    def _make_request(self, **meta):
        rf = RequestFactory()
        request = rf.get("/")
        request.META.update(meta)
        return request

    # --- CF-Connecting-IP (primary source) ---

    def test_cf_connecting_ip_used_when_present(self):
        """CF-Connecting-IP wins over any X-Forwarded-For value."""
        request = self._make_request(
            HTTP_CF_CONNECTING_IP="1.2.3.4",
            HTTP_X_FORWARDED_FOR="5.6.7.8, 172.18.0.1",
        )
        assert get_client_ip(request) == "1.2.3.4"

    def test_cf_connecting_ip_ipv6(self):
        request = self._make_request(HTTP_CF_CONNECTING_IP="2a09:bac3:3759:278::3f:dd")
        assert get_client_ip(request) == "2a09:bac3:3759:278::3f:dd"

    def test_cf_connecting_ip_malformed_falls_through(self):
        """If CF-Connecting-IP is somehow malformed, fall back to XFF."""
        request = self._make_request(
            HTTP_CF_CONNECTING_IP="not-an-ip",
            HTTP_X_FORWARDED_FOR="81.141.119.30, 172.18.0.1",
            REMOTE_ADDR="10.0.0.5",
        )
        # Should land on rightmost valid XFF entry, not REMOTE_ADDR
        assert get_client_ip(request) == "172.18.0.1"

    # --- X-Forwarded-For fallback (rightmost valid entry) ---

    def test_xff_rightmost_used_without_cf_header(self):
        """Without CF-Connecting-IP, use rightmost XFF (nearest trusted proxy)."""
        request = self._make_request(HTTP_X_FORWARDED_FOR="81.141.119.30, 172.18.0.1, 172.18.0.2")
        assert get_client_ip(request) == "172.18.0.2"

    def test_xff_single_entry(self):
        request = self._make_request(HTTP_X_FORWARDED_FOR="192.168.1.1")
        assert get_client_ip(request) == "192.168.1.1"

    def test_xff_ipv6_rightmost(self):
        request = self._make_request(HTTP_X_FORWARDED_FOR="2a09:bac3:3759:278::3f:dd, 172.18.0.1")
        assert get_client_ip(request) == "172.18.0.1"

    def test_xff_spoofing_bypass_prevented(self):
        """Core security regression: attacker injects a fake leftmost entry.
        Cloudflare appends the real IP but does NOT strip the injected entry.
        The fix must return the real (rightmost) IP, not the spoofed leftmost."""
        request = self._make_request(
            HTTP_X_FORWARDED_FOR="1.1.1.1, 5.5.5.5",  # 1.1.1.1 is attacker-injected
        )
        # Real client IP is 5.5.5.5 (appended by Cloudflare)
        assert get_client_ip(request) == "5.5.5.5"
        assert get_client_ip(request) != "1.1.1.1"

    def test_xff_skips_malformed_entries_from_right(self):
        """Malformed rightmost entries are skipped; search continues leftward."""
        request = self._make_request(
            HTTP_X_FORWARDED_FOR="81.141.119.30, 172.18.0.1, bad-entry",
            REMOTE_ADDR="10.0.0.9",
        )
        assert get_client_ip(request) == "172.18.0.1"

    def test_xff_all_malformed_falls_back_to_remote_addr(self):
        request = self._make_request(HTTP_X_FORWARDED_FOR="not-an-ip, also-bad", REMOTE_ADDR="172.18.0.2")
        assert get_client_ip(request) == "172.18.0.2"

    # --- REMOTE_ADDR fallback ---

    def test_no_forwarded_for_uses_remote_addr(self):
        request = self._make_request(REMOTE_ADDR="10.0.0.1")
        assert get_client_ip(request) == "10.0.0.1"

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
