"""Tests for core middleware functions."""

import pytest
from django.test import RequestFactory

from apps.core.middleware import get_client_ip


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
