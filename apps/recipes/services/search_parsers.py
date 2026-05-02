"""
HTML/URL parsing helpers for recipe search.

Extracted from RecipeSearch to keep search.py focused on orchestration.
All functions are module-level (no class needed).
"""

import logging
import re
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from apps.recipes.services.search import SearchResult
from apps.recipes.services.search_classifiers import (
    get_url_signal,
    looks_like_recipe_title,
)

logger = logging.getLogger(__name__)


def find_link(element) -> Optional[tuple]:
    """Find recipe link in an HTML element.

    Returns:
        Tuple of (link_element, url) if found, None otherwise.
    """
    link = element.find("a", href=True)
    if not link:
        link = element if element.name == "a" and element.get("href") else None
    if not link:
        return None

    url = link.get("href", "")
    if not url:
        return None

    return link, url


def extract_title(element, link) -> str:
    """Extract title from element with multiple fallback strategies.

    Uses separator=" " so nested metadata spans (e.g. prep-time) don't
    bleed into the title without whitespace.
    """
    title_el = element.find(["h2", "h3", "h4", ".title", '[class*="title"]'])
    if title_el:
        title = title_el.get_text(separator=" ", strip=True)
        if title:
            return _strip_title_metadata(title)

    title = link.get_text(separator=" ", strip=True)
    if title:
        return _strip_title_metadata(title)

    return link.get("title", "") or link.get("aria-label", "")


# Strips trailing time metadata, e.g. "30 mins", "1 hr 30 mins".
_TRAILING_TIME_RE = re.compile(
    r"\s+\d+\s*(?:hr?s?|hour[s]?|min(?:ute)?[s]?)(?:\s+\d+\s*(?:min(?:ute)?[s]?))?$",
    re.IGNORECASE,
)


def _strip_title_metadata(title: str) -> str:
    """Strip trailing time/duration metadata from a recipe card title."""
    return _TRAILING_TIME_RE.sub("", title).strip()


def extract_rating(title: str) -> tuple[str, Optional[int]]:
    """Extract and strip rating count from title.

    Handles patterns like "Recipe Name1,392Ratings".

    Returns:
        Tuple of (cleaned_title, rating_count).
    """
    rating_match = re.search(r"([\d,]+)\s*[Rr]atings?\s*$", title)
    if not rating_match:
        return title, None

    rating_str = rating_match.group(1).replace(",", "")
    try:
        rating_count = int(rating_str)
        cleaned_title = title[: rating_match.start()].strip()
        return cleaned_title, rating_count
    except ValueError:
        return title, None


def extract_description(element) -> str:
    """Extract description from element."""
    desc_el = element.find(["p", ".description", '[class*="description"]'])
    if desc_el:
        return desc_el.get_text(strip=True)[:200]
    return ""


def parse_srcset(srcset: str) -> list[tuple[str, int]]:
    """Parse srcset string into (url, width) pairs.

    Handles srcset format: "url1 100w, url2 200w"
    URLs may contain commas (e.g. resize=93,84) so we split on
    the width descriptor pattern rather than plain commas.
    """
    results = []
    for match in re.finditer(r"(https?://\S+?)\s+(\d+)w", srcset):
        url = match.group(1)
        width = int(match.group(2))
        results.append((url, width))
    return results


def _collect_srcset_strings(element) -> list[str]:
    """Collect non-WebP srcset strings from <picture><source> and <img>."""
    srcsets = []
    picture = element.find("picture")
    if picture:
        for src in picture.find_all("source"):
            srcset = src.get("srcset", "")
            if srcset and "webp" not in (src.get("type") or "").lower():
                srcsets.append(srcset)
    img = element.find("img")
    if img and img.get("srcset", ""):
        srcsets.append(img["srcset"])
    return srcsets


def best_url_from_srcset(element, base_url: str) -> str:
    """Extract the largest non-WebP image URL from srcset attributes."""
    entries = [e for s in _collect_srcset_strings(element) for e in parse_srcset(s)]
    if not entries:
        return ""
    best_url, _ = max(entries, key=lambda e: e[1])
    return urljoin(base_url, best_url)


def extract_image(element, base_url: str) -> str:
    """Extract image URL with multiple fallback strategies.

    Tries srcset (for largest image), then src, data-src, data-lazy-src.
    Handles <picture><source srcset> patterns used by modern sites.
    """
    # Try to get the best image from srcset first (larger than thumbnail)
    srcset_url = best_url_from_srcset(element, base_url)
    if srcset_url:
        return srcset_url

    # Fallback to img src attributes
    img = element.find("img")
    if not img:
        return ""

    image_url = img.get("src") or img.get("data-src") or img.get("data-lazy-src", "")
    if image_url:
        return urljoin(base_url, image_url)
    return ""


def extract_result_from_element(
    element,
    host: str,
    base_url: str,
) -> Optional[SearchResult]:
    """Extract search result data from an HTML element."""
    # Find and validate link
    link_result = find_link(element)
    if not link_result:
        return None
    link, url = link_result

    # Make URL absolute and get signal strength
    url = urljoin(base_url, url)
    url_signal = get_url_signal(url, host)
    if url_signal in ("strong_exclude", "reject"):
        return None

    # Extract title
    title = extract_title(element, link)
    if not title:
        return None

    # Extract and strip rating from title
    title, rating_count = extract_rating(title)

    # Title may have become empty after stripping rating (QA-053)
    if not title:
        return None

    # Filter non-recipe content by title (012-filter-search-results)
    if not looks_like_recipe_title(title, url_signal):
        logger.debug("Filtered non-recipe title: %s (%s)", title, url)
        return None

    image_url = extract_image(element, base_url)
    description = extract_description(element)

    # Neutral URLs must have both image AND description — recipe cards almost
    # always do; editorial/article results often lack one or both.
    if url_signal == "neutral" and (not image_url or not description):
        logger.debug("Filtered neutral URL missing image or description: %s (%s)", title, url)
        return None

    return SearchResult(
        url=url,
        title=title[:200],
        host=host,
        image_url=image_url,
        description=description,
        rating_count=rating_count,
    )


def _parse_articles(
    soup: BeautifulSoup,
    host: str,
    base_url: str,
) -> list[SearchResult]:
    """Strategy: extract results from <article> elements."""
    _ext = extract_result_from_element
    return [r for el in soup.find_all("article")[:30] if (r := _ext(el, host, base_url))]


def _parse_cards(
    soup: BeautifulSoup,
    host: str,
    base_url: str,
) -> list[SearchResult]:
    """Strategy: extract results from card-like div elements."""
    _ext = extract_result_from_element
    for sel in ('[class*="recipe-card"]', '[class*="card"]', '[class*="result"]', '[class*="item"]'):
        results = [r for el in soup.select(sel)[:30] if (r := _ext(el, host, base_url))]
        if results:
            return results
    return []


def _parse_links(
    soup: BeautifulSoup,
    host: str,
    base_url: str,
) -> list[SearchResult]:
    """Strategy: extract results from links that look like recipe URLs."""
    results = []
    for link in soup.find_all("a", href=True)[:100]:
        url = urljoin(base_url, link.get("href", ""))
        url_signal = get_url_signal(url, host)
        if url_signal not in ("strong_include", "neutral"):
            continue
        title = link.get_text(strip=True)
        if title and len(title) > 5 and looks_like_recipe_title(title, url_signal):
            results.append(SearchResult(url=url, title=title[:200], host=host))
    return results


def fallback_parse(
    soup: BeautifulSoup,
    host: str,
    base_url: str,
) -> list[SearchResult]:
    """Fallback parser for sites without a specific selector.

    Tries article elements, card-like divs, then bare recipe links.
    """
    for strategy in (_parse_articles, _parse_cards, _parse_links):
        results = strategy(soup, host, base_url)
        if results:
            return results
    return []
