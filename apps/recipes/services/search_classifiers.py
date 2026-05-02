"""URL- and title-level classifiers used by the recipe search parser.

Extracted from `search_parsers.py` to keep that file under the per-file size
budget. The classifiers decide whether a candidate result represents a recipe
detail page rather than an article, gallery, or category index.
"""

import re
from typing import Optional
from urllib.parse import urlparse


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


def _check_exclusion_patterns(path: str) -> bool:
    """Return True if path matches any exclusion pattern."""
    return any(pattern.search(path) for pattern in _EXCLUDE_PATTERNS)


def _check_recipe_patterns(path: str) -> bool:
    """Return True if path matches any recipe pattern."""
    return any(pattern.search(path) for pattern in _RECIPE_PATTERNS)


def _skinnytaste_signal(path: str) -> Optional[str]:
    """Skinnytaste publishes recipes at /<slug>/ with no description on the
    search page, which the generic neutral-URL filter would reject. Treat any
    top-level hyphenated slug as a strong recipe signal; exclusion patterns
    above already strip /about/, /category/, etc.
    """
    segments = [s for s in path.split("/") if s]
    if len(segments) == 1 and len(segments[0]) > 15 and segments[0].count("-") >= 2:
        return "strong_include"
    return None


# Site-specific rules: host → callable returning signal or None
_SITE_RULES: dict[str, callable] = {
    "allrecipes.com": lambda path: "reject" if "/recipe/" not in path else None,
    "skinnytaste.com": _skinnytaste_signal,
}


def _check_site_rules(host: str, path: str) -> Optional[str]:
    """Apply site-specific rules. Returns a signal string or None."""
    for domain, rule in _SITE_RULES.items():
        if host == domain or host.endswith(f".{domain}"):
            return rule(path)
    return None


def _check_path_heuristics(path: str) -> str:
    """Apply heuristic fallbacks for paths with no strong signal.

    Returns "neutral" or "reject".
    """
    segments = [s for s in path.split("/") if s]
    if len(segments) >= 2 and len(path) > 20:
        return "neutral"
    if len(segments) == 1 and len(path) > 15 and path.count("-") >= 2:
        return "neutral"
    return "reject"


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

    if _check_exclusion_patterns(path):
        return "strong_exclude"

    site_signal = _check_site_rules(host, path)
    if site_signal is not None:
        return site_signal

    if _check_recipe_patterns(path):
        return "strong_include"

    return _check_path_heuristics(path)


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
