"""URL validation utilities for SSRF protection."""

import ipaddress
import socket
from urllib.parse import urlparse

BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def is_blocked_ip(ip_str):
    """Check if an IP address falls within any blocked range."""
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    return any(addr in network for network in BLOCKED_NETWORKS)


def resolve_hostname(hostname):
    """Resolve a hostname to its IP address via DNS."""
    try:
        results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise ValueError(f"Could not resolve hostname: {hostname}") from e
    if not results:
        raise ValueError(f"Could not resolve hostname: {hostname}")
    return results[0][4][0]


def validate_url(url):
    """Validate a URL for SSRF protection. Returns the URL or raises ValueError."""
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"URL scheme not allowed: {parsed.scheme}")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL has no hostname")

    ip_str = resolve_hostname(hostname)

    if is_blocked_ip(ip_str):
        raise ValueError("URL not allowed: resolves to blocked IP range.")

    return url
