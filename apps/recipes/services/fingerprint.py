"""
Browser fingerprint configuration for web scraping.

Uses curl_cffi's browser impersonation feature to bypass anti-bot detection.
This module centralizes all fingerprint-related configuration for maintainability.

Maintenance Notes:
- Browser profiles should be updated periodically as curl_cffi releases new versions
- Current profiles are based on curl_cffi >= 0.11
- Check https://curl-cffi.readthedocs.io/en/latest/impersonate/targets.html for updates
- If a browser version becomes unavailable, remove it from the fallback list
"""

import random

# Primary browser profiles to impersonate
# These are the most common browsers that recipe sites expect
# Order matters: Chrome first as most compatible, then Safari, then Firefox
BROWSER_PROFILES = [
    "chrome136",  # Latest Chrome (most compatible with majority of sites)
    "safari184",  # Latest Safari desktop
    "firefox133",  # Latest Firefox
    "chrome131",  # Fallback Chrome version
]

# Convenience aliases that auto-update to latest versions
# Use these if you want curl_cffi to always use the newest fingerprint
BROWSER_ALIASES = {
    "chrome": "chrome",  # Auto-resolves to latest Chrome
    "safari": "safari",  # Auto-resolves to latest Safari
    "firefox": "firefox133",  # No alias for Firefox in curl_cffi
}

# Mobile profiles for sites that serve different content to mobile
MOBILE_PROFILES = [
    "safari184_ios",  # Latest iOS Safari
    "chrome131_android",  # Android Chrome
]

# Request timing configuration (in seconds)
# Randomizing delays helps avoid bot detection patterns
MIN_DELAY = 0.5  # Minimum delay between requests to same domain
MAX_DELAY = 2.5  # Maximum delay between requests to same domain


def get_random_profile() -> str:
    """
    Get a random browser profile from the pool.

    Returns a weighted random choice favoring Chrome (most compatible).
    """
    weights = [50, 25, 15, 10]  # Chrome 136, Safari 184, Firefox 133, Chrome 131
    return random.choices(BROWSER_PROFILES, weights=weights)[0]


def get_random_delay() -> float:
    """
    Get a random delay for rate limiting.

    Returns a random float between MIN_DELAY and MAX_DELAY.
    Uses slight randomization to avoid predictable patterns.
    """
    return random.uniform(MIN_DELAY, MAX_DELAY)


def get_fallback_profiles(exclude: str = None) -> list[str]:
    """
    Get list of fallback profiles, optionally excluding one.

    Args:
        exclude: Profile to exclude (e.g., if it just failed)

    Returns:
        List of profile names to try
    """
    profiles = BROWSER_PROFILES.copy()
    if exclude and exclude in profiles:
        profiles.remove(exclude)
    return profiles
