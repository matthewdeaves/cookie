"""
HTML/URL parsing helpers for recipe search.

Extracted from RecipeSearch to keep search.py focused on orchestration.
All functions are module-level (no class needed).
"""

import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from apps.recipes.services.search import SearchResult

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

    Tries: heading elements, link text, title/aria-label attributes.
    """
    title_el = element.find(["h2", "h3", "h4", ".title", '[class*="title"]'])
    if title_el:
        title = title_el.get_text(strip=True)
        if title:
            return title

    title = link.get_text(strip=True)
    if title:
        return title

    return link.get("title", "") or link.get("aria-label", "")


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


def best_url_from_srcset(element, base_url: str) -> str:
    """Extract the largest non-WebP image URL from srcset attributes.

    Checks <picture><source srcset> and <img srcset>.
    """
    srcset_candidates = []

    # Check <picture><source srcset> (prefer non-WebP sources)
    picture = element.find("picture")
    if picture:
        for source in picture.find_all("source"):
            source_type = (source.get("type") or "").lower()
            if "webp" in source_type:
                continue
            srcset = source.get("srcset", "")
            if srcset:
                srcset_candidates.append(srcset)

    # Check <img srcset>
    img = element.find("img")
    if img:
        srcset = img.get("srcset", "")
        if srcset:
            srcset_candidates.append(srcset)

    # Parse srcset entries and pick the largest
    best_url = ""
    best_width = 0
    for srcset in srcset_candidates:
        for url, width in parse_srcset(srcset):
            if width > best_width:
                best_width = width
                best_url = url

    if best_url:
        return urljoin(base_url, best_url)
    return ""


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

    # Field validation: neutral URL results must have both image AND description.
    # Real recipe cards from search pages almost always have both.
    # Editorial/article results often lack one or both.
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


def fallback_parse(
    soup: BeautifulSoup,
    host: str,
    base_url: str,
) -> list[SearchResult]:
    """
    Fallback parser for sites without a specific selector.

    Looks for common patterns in recipe search results.
    """
    results = []

    # Strategy 1: Look for article elements with links
    for article in soup.find_all("article")[:30]:
        result = extract_result_from_element(article, host, base_url)
        if result:
            results.append(result)

    if results:
        return results

    # Strategy 2: Look for card-like divs
    card_selectors = [
        '[class*="recipe-card"]',
        '[class*="card"]',
        '[class*="result"]',
        '[class*="item"]',
    ]
    for selector in card_selectors:
        for card in soup.select(selector)[:30]:
            result = extract_result_from_element(card, host, base_url)
            if result:
                results.append(result)
        if results:
            return results

    # Strategy 3: Look for links that look like recipe URLs
    for link in soup.find_all("a", href=True)[:100]:
        url = urljoin(base_url, link.get("href", ""))
        url_signal = get_url_signal(url, host)
        if url_signal in ("strong_include", "neutral"):
            title = link.get_text(strip=True)
            if title and len(title) > 5 and looks_like_recipe_title(title, url_signal):
                results.append(
                    SearchResult(
                        url=url,
                        title=title[:200],
                        host=host,
                    )
                )

    return results


# Compiled patterns for looks_like_recipe_url (avoid recompiling per call)
_RECIPE_PATTERNS = [
    re.compile(p)
    for p in [
        r"/recipe[s]?/",
        r"/dish/",
        r"/food/",
        r"/cooking/",
        r"/\d+/",
        r"-recipe/?$",
        r"/a\d+/",
        r"/food-cooking/",
    ]
]

_EXCLUDE_PATTERNS = [
    re.compile(p)
    for p in [
        r"/search",
        r"/tag/",
        r"/category/",
        r"/author/",
        r"/profile/",
        r"/user/",
        r"/about",
        r"/contact",
        r"/privacy",
        r"/terms",
        r"/newsletter",
        r"/subscribe",
        # Article/blog paths (QA-053)
        r"/article/",
        r"/articles/",
        r"/blog/",
        r"/post/",
        r"/posts/",
        r"/news/",
        r"/story/",
        r"/stories/",
        r"/feature/",
        r"/features/",
        r"/guide/",
        r"/guides/",
        r"/review/",
        r"/reviews/",
        r"/roundup/",
        r"/list/",
        r"/listicle/",
        # Video paths (QA-053)
        r"/video/",
        r"/videos/",
        r"/watch/",
        r"/watch\?",
        r"/embed/",
        r"/player/",
        r"/clip/",
        r"/clips/",
        r"/episode/",
        r"/episodes/",
        r"/series/",
        r"/show/",
        r"/shows/",
        r"/gallery/",
        r"/galleries/",
        r"/slideshow/",
        r"/photo-gallery/",
        # Index/listing pages (QA-053)
        r"/seasons?(?:/|$)",
        r"/cuisines?(?:/|$)",
        r"/ingredients?(?:/|$)",
        r"/collections?(?:/|$)",
        r"/occasions?(?:/|$)",
        r"/courses?(?:/|$)",
        r"/diets?(?:/|$)",
        r"/techniques?(?:/|$)",
        r"/chefs?(?:/|$)",
        r"/dishes(?:/|$)",
        r"/menus?(?:/|$)",
        r"/meal-plans?(?:/|$)",
    ]
]


def get_url_signal(url: str, host: str) -> str:
    """Determine URL signal strength for recipe filtering.

    Returns:
        "strong_exclude" - URL matches exclusion patterns (articles, blogs, etc.)
        "strong_include" - URL matches recipe patterns (/recipe/, /recipes/, etc.)
        "neutral" - URL passes heuristics but has no strong signal
        "reject" - URL fails all checks (wrong host, too short, etc.)
    """
    parsed = urlparse(url)

    if host not in parsed.netloc:
        return "reject"

    path = parsed.path.lower()

    for pattern in _EXCLUDE_PATTERNS:
        if pattern.search(path):
            return "strong_exclude"

    # Site-specific: AllRecipes requires /recipe/ path
    if "allrecipes.com" in host and "/recipe/" not in path:
        return "reject"

    for pattern in _RECIPE_PATTERNS:
        if pattern.search(path):
            return "strong_include"

    # Heuristic fallbacks → neutral signal
    segments = [s for s in path.split("/") if s]
    if len(segments) >= 2 and len(path) > 20:
        return "neutral"

    if len(segments) == 1 and len(path) > 15 and path.count("-") >= 2:
        return "neutral"

    return "reject"


def looks_like_recipe_url(url: str, host: str) -> bool:
    """Check if a URL looks like a recipe detail page."""
    signal = get_url_signal(url, host)
    return signal in ("strong_include", "neutral")


# Strong editorial patterns — always reject even if recipe words present
# These are clearly article/editorial headlines, not recipe titles
_STRONG_EDITORIAL_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bdeserves?\s+a\s+(?:gold|silver|bronze)\s+medal\b",
        r"\bis\s+a\s+weeknight\s+winner\b",
        r"\btop\s+trending\s+recipe\s+of\s+\d{4}\b",
        r"\binsanely\s+awesome\b",
        r"\bmost\s+beautiful\s+destination\b",
        r"\bbest\s+time\s+to\s+book\b",
    ]
]

# Mild editorial patterns — rejected unless recipe-context words present
_EDITORIAL_TITLE_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        # Listicles: "Top 10...", "5 Best...", "7 Reasons..."
        r"^(?:the\s+)?(?:top\s+)?\d+\s+(?:best|worst|things|reasons|ways|places|tips|tricks|destinations|restaurants|spots|cities|towns)\b",
        # Travel/destination content
        r"\btravel\s+guide\b",
        r"\bbest\s+destinations?\b",
        r"\bplaces?\s+to\s+visit\b",
        r"\bwhere\s+to\s+(?:eat|go|stay|travel)\b",
        r"\bbook\s+(?:your\s+)?(?:thanksgiving|christmas|holiday)\s+travel\b",
        # Review/editorial
        r"^review\s*:",
        r"\b(?:product|book|restaurant|movie|hotel|app)\s+review\b",
        # News/trending headers
        r"^(?:news|breaking|update|trending)\s*:",
        # Meta/navigation pages
        r"^(?:about\s+us|contact\s+us|privacy\s+policy|terms\s+of|cookie\s+policy|subscribe|newsletter|sign\s+up|log\s+in)\b",
    ]
]

# Recipe-context words that override mild editorial title patterns
_RECIPE_CONTEXT_PATTERN = re.compile(
    r"\b(?:recipe[s]?|cook(?:ing|ed)?|bake[ds]?|baking|roast(?:ed|ing)?|"
    r"grill(?:ed|ing)?|how\s+to\s+(?:make|cook|bake|prepare)|homemade|"
    r"ingredient[s]?|from\s+scratch|step.by.step|easy\s+(?:to\s+)?make)\b",
    re.IGNORECASE,
)


def looks_like_recipe_title(title: str, url_signal: str) -> bool:
    """Check if a search result title looks like recipe content.

    Uses tiered resolution with URL signal strength:
    - strong_include URLs: always pass (recipe URL overrides title concerns)
    - neutral URLs: evaluated by title patterns
    - Strong editorial patterns always reject (even with recipe words)
    - Mild editorial patterns rejected unless recipe-context words present
    """
    if url_signal == "strong_include":
        return True

    title_stripped = title.strip()
    if not title_stripped:
        return False

    # Strong editorial patterns always reject
    for pattern in _STRONG_EDITORIAL_PATTERNS:
        if pattern.search(title_stripped):
            return False

    # Mild editorial patterns rejected unless recipe-context words present
    for pattern in _EDITORIAL_TITLE_PATTERNS:
        if pattern.search(title_stripped):
            if _RECIPE_CONTEXT_PATTERN.search(title_stripped):
                return True
            return False

    return True
