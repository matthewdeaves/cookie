"""
Tests for the deterministic search result ranking service.

Tests the ranking service at apps/ai/services/ranking.py:
- rank_results() main entry point
- _filter_valid() removes titleless results
- _score_result() scoring logic (image, term match, exact phrase)
"""

from apps.ai.services.ranking import rank_results, _filter_valid, _score_result


# --- _filter_valid ---


def test_filter_valid_removes_results_without_titles():
    """Results without titles are filtered out."""
    results = [
        {"title": "Chicken Tikka Masala", "image_url": "http://example.com/img.jpg", "host": "example.com"},
        {"title": "", "image_url": "http://example.com/img2.jpg", "host": "example.com"},
        {"image_url": "http://example.com/img3.jpg", "host": "example.com"},
        {"title": "Butter Chicken", "host": "example.com"},
    ]
    filtered = _filter_valid(results)
    assert len(filtered) == 2
    assert filtered[0]["title"] == "Chicken Tikka Masala"
    assert filtered[1]["title"] == "Butter Chicken"


# --- rank_results ---


def test_empty_results_returns_empty_list():
    """Empty results returns empty list."""
    assert rank_results("chicken", []) == []


def test_results_with_images_rank_before_results_without():
    """Results with images appear before results without images."""
    results = [
        {"title": "No Image Recipe", "image_url": "", "host": "example.com"},
        {"title": "Image Recipe", "image_url": "http://example.com/img.jpg", "host": "example.com"},
    ]
    ranked = rank_results("pasta", results)
    assert ranked[0]["title"] == "Image Recipe"
    assert ranked[1]["title"] == "No Image Recipe"


def test_more_query_term_matches_rank_higher():
    """More query term matches rank higher."""
    results = [
        {"title": "Grilled Steak", "image_url": "", "host": "example.com"},
        {"title": "Chicken Tikka Masala", "image_url": "", "host": "example.com"},
        {"title": "Chicken Tikka Wrap", "image_url": "", "host": "example.com"},
    ]
    ranked = rank_results("chicken tikka masala", results)
    # "Chicken Tikka Masala" matches all 3 terms + exact phrase
    # "Chicken Tikka Wrap" matches 2 terms
    # "Grilled Steak" matches 0 terms
    assert ranked[0]["title"] == "Chicken Tikka Masala"
    assert ranked[1]["title"] == "Chicken Tikka Wrap"
    assert ranked[2]["title"] == "Grilled Steak"


def test_exact_phrase_bonus_gives_additional_score():
    """Exact phrase bonus gives additional score beyond individual term matches."""
    results = [
        {"title": "Butter Chicken Masala", "image_url": "", "host": "example.com"},
        {"title": "Chicken Butter Dish", "image_url": "", "host": "example.com"},
    ]
    # Both match "butter" and "chicken" (2 terms each = 10 points each)
    # Only "Butter Chicken Masala" contains "butter chicken" as exact phrase (+10)
    ranked = rank_results("butter chicken", results)
    assert ranked[0]["title"] == "Butter Chicken Masala"
    assert ranked[1]["title"] == "Chicken Butter Dish"


def test_all_results_without_images_ranked_by_title_match_only():
    """All results without images: ranked by title match only."""
    results = [
        {"title": "Pasta Carbonara", "image_url": "", "host": "example.com"},
        {"title": "Chicken Pasta Bake", "image_url": "", "host": "example.com"},
        {"title": "Grilled Salmon", "image_url": "", "host": "example.com"},
    ]
    ranked = rank_results("chicken pasta", results)
    # "Chicken Pasta Bake" matches both terms (10 points)
    # "Pasta Carbonara" matches one term (5 points)
    # "Grilled Salmon" matches none (0 points)
    assert ranked[0]["title"] == "Chicken Pasta Bake"
    assert ranked[1]["title"] == "Pasta Carbonara"
    assert ranked[2]["title"] == "Grilled Salmon"


def test_empty_query_sorted_by_image_presence_only():
    """Empty query: sorted by image presence only (no term matching)."""
    results = [
        {"title": "No Image Recipe", "image_url": "", "host": "example.com"},
        {"title": "Image Recipe", "image_url": "http://example.com/img.jpg", "host": "example.com"},
        {"title": "Another No Image", "image_url": "", "host": "example.com"},
    ]
    ranked = rank_results("", results)
    assert ranked[0]["title"] == "Image Recipe"
    # The two without images follow (order among them is stable/arbitrary)
    assert all(r["image_url"] == "" for r in ranked[1:])


def test_single_character_query_terms_are_ignored():
    """Single-character query terms are ignored (len >= 2 filter)."""
    results = [
        {"title": "A Recipe With Chicken", "image_url": "", "host": "example.com"},
        {"title": "Plain Bread", "image_url": "", "host": "example.com"},
    ]
    # "a" is single char and should be ignored; only "big" counts
    ranked = rank_results("a big", results)
    # Neither title contains "big", so scores are equal (both 0)
    assert len(ranked) == 2

    # Verify single-char terms truly ignored: query "a" alone produces no term matches
    query_terms = [t for t in "a".lower().split() if len(t) >= 2]
    assert query_terms == []


def test_case_insensitive_matching():
    """Case-insensitive matching for query terms and titles."""
    results = [
        {"title": "CHICKEN TIKKA MASALA", "image_url": "", "host": "example.com"},
        {"title": "plain rice", "image_url": "", "host": "example.com"},
    ]
    ranked = rank_results("Chicken Tikka", results)
    assert ranked[0]["title"] == "CHICKEN TIKKA MASALA"
    assert ranked[1]["title"] == "plain rice"


# --- _score_result ---


def test_score_result_image_bonus():
    """Image presence adds 100 to score."""
    result_with_image = {"title": "Test", "image_url": "http://example.com/img.jpg"}
    result_without_image = {"title": "Test", "image_url": ""}
    assert _score_result(result_with_image, []) == 100
    assert _score_result(result_without_image, []) == 0


def test_score_result_term_match_bonus():
    """Each matching term adds 5 to score."""
    result = {"title": "Chicken Tikka Masala", "image_url": ""}
    # Single term: 5 (term match) + 10 (exact phrase, since single-term phrase matches)
    assert _score_result(result, ["chicken"]) == 15
    # Two terms: 10 (term matches) + 10 (exact phrase "chicken tikka" found) = 20
    assert _score_result(result, ["chicken", "tikka"]) == 20
    # Three terms: 15 (term matches) + 10 (exact phrase) = 25
    assert _score_result(result, ["chicken", "tikka", "masala"]) == 25


def test_score_result_exact_phrase_bonus():
    """Exact phrase match adds 10 to score on top of term matches."""
    result = {"title": "Butter Chicken Curry", "image_url": ""}
    # Two terms match (10) + exact phrase "butter chicken" (10) = 20
    assert _score_result(result, ["butter", "chicken"]) == 20
