"""Tests for URL- and title-level classifiers used by the recipe parser."""

from apps.recipes.services.search_classifiers import (
    get_url_signal,
    looks_like_recipe_title,
    looks_like_recipe_url,
)


class TestSearchHelpers:
    """Tests for search helper methods."""

    def test_looks_like_recipe_url_recipe_path(self):
        """Test URL with /recipe/ in path is detected."""
        assert (
            looks_like_recipe_url("https://allrecipes.com/recipe/12345/chocolate-chip-cookies/", "allrecipes.com")
            is True
        )

    def test_looks_like_recipe_url_recipes_path(self):
        """Test URL with /recipes/ in path is detected."""
        assert looks_like_recipe_url("https://food52.com/recipes/12345-cookies", "food52.com") is True

    def test_looks_like_recipe_url_numeric_id(self):
        """Test URL with numeric ID in path is detected."""
        assert looks_like_recipe_url("https://example.com/12345/yummy-cookies", "example.com") is True

    def test_looks_like_recipe_url_wrong_host(self):
        """Test URL from wrong host is rejected."""
        assert looks_like_recipe_url("https://different-site.com/recipe/123", "allrecipes.com") is False

    def test_looks_like_recipe_url_search_page(self):
        """Test search page URLs are rejected."""
        assert looks_like_recipe_url("https://allrecipes.com/search?q=cookies", "allrecipes.com") is False

    def test_looks_like_recipe_url_category_page(self):
        """Test category page URLs are rejected."""
        assert looks_like_recipe_url("https://allrecipes.com/category/desserts/", "allrecipes.com") is False

    def test_looks_like_recipe_url_author_page(self):
        """Test author page URLs are rejected."""
        assert looks_like_recipe_url("https://allrecipes.com/author/chef-john/", "allrecipes.com") is False

    def test_looks_like_recipe_url_long_path(self):
        """Test that long paths with multiple segments are accepted."""
        assert (
            looks_like_recipe_url("https://example.com/food/desserts/chocolate-chip-cookies-recipe", "example.com")
            is True
        )


class TestGetUrlSignal:
    """Tests for get_url_signal() function (T008)."""

    def test_strong_exclude_article_path(self):
        assert get_url_signal("https://example.com/article/trending-food", "example.com") == "strong_exclude"

    def test_strong_exclude_blog_path(self):
        assert get_url_signal("https://example.com/blog/my-kitchen-tips", "example.com") == "strong_exclude"

    def test_strong_exclude_gallery_path(self):
        assert get_url_signal("https://example.com/gallery/food-photos", "example.com") == "strong_exclude"

    def test_strong_exclude_video_path(self):
        assert get_url_signal("https://example.com/video/cooking-tutorial", "example.com") == "strong_exclude"

    def test_strong_include_recipe_path(self):
        assert get_url_signal("https://example.com/recipe/123/chicken-tagine", "example.com") == "strong_include"

    def test_strong_include_recipes_path(self):
        assert get_url_signal("https://example.com/recipes/pasta-carbonara", "example.com") == "strong_include"

    def test_strong_include_food_path(self):
        assert get_url_signal("https://example.com/food/best-cookies", "example.com") == "strong_include"

    def test_neutral_slug_style_url(self):
        assert get_url_signal("https://example.com/googles-top-trending-recipe-of-2024", "example.com") == "neutral"

    def test_neutral_multi_segment_path(self):
        # This path ends with "-recipe" which matches _RECIPE_PATTERNS
        assert (
            get_url_signal("https://example.com/food-section/desserts/chocolate-cake-recipe", "example.com")
            == "strong_include"
        )

    def test_neutral_multi_segment_no_recipe_pattern(self):
        assert (
            get_url_signal("https://example.com/food-section/desserts/chocolate-cake-delight", "example.com")
            == "neutral"
        )

    def test_reject_wrong_host(self):
        assert get_url_signal("https://other.com/recipe/123", "example.com") == "reject"

    def test_reject_short_path(self):
        assert get_url_signal("https://example.com/x", "example.com") == "reject"

    def test_backward_compat_looks_like_recipe_url(self):
        """Ensure looks_like_recipe_url still works as before."""
        assert looks_like_recipe_url("https://example.com/recipe/123/cookies", "example.com") is True
        assert looks_like_recipe_url("https://example.com/article/trending", "example.com") is False

    def test_skinnytaste_slug_treated_as_strong_include(self):
        # Skinnytaste publishes recipes at /<slug>/ with no excerpt on the
        # search page; the site rule must keep them out of the neutral filter.
        assert (
            get_url_signal(
                "https://www.skinnytaste.com/chicken-and-dumplings-with-leeks-mushrooms-and-peas/",
                "skinnytaste.com",
            )
            == "strong_include"
        )

    def test_skinnytaste_excluded_paths_still_rejected(self):
        # Exclusion patterns run before site rules.
        assert (
            get_url_signal("https://www.skinnytaste.com/about-gina/", "skinnytaste.com") == "strong_exclude"
        )

    def test_skinnytaste_short_root_path_falls_through(self):
        # Short single-segment paths shouldn't be promoted to strong_include.
        assert (
            get_url_signal("https://www.skinnytaste.com/shop/", "skinnytaste.com") == "reject"
        )


class TestLooksLikeRecipeTitle:
    """Tests for looks_like_recipe_title() function (T009, T010, T012-T016)."""

    # --- Legitimate recipe titles should PASS ---

    def test_simple_recipe_title_passes(self):
        assert looks_like_recipe_title("Chicken Tagine", "neutral") is True

    def test_pasta_recipe_passes(self):
        assert looks_like_recipe_title("Pasta Carbonara", "neutral") is True

    def test_short_title_passes(self):
        assert looks_like_recipe_title("Soup", "neutral") is True

    def test_tiktok_recipe_passes(self):
        assert looks_like_recipe_title("TikTok Feta Pasta", "neutral") is True

    def test_cowboy_caviar_passes(self):
        assert looks_like_recipe_title("Cowboy Caviar", "neutral") is True

    def test_recipe_with_brand_name_passes(self):
        assert looks_like_recipe_title("Google's Famous Cookie Recipe", "neutral") is True

    # --- Recipe-context override: editorial pattern + recipe word = PASS ---

    def test_listicle_with_recipe_word_passes(self):
        assert looks_like_recipe_title("Top 10 Easy Cookie Recipes", "neutral") is True

    def test_listicle_with_cooking_word_passes(self):
        assert looks_like_recipe_title("5 Best Ways to Cook Chicken", "neutral") is True

    def test_listicle_with_baking_word_passes(self):
        assert looks_like_recipe_title("7 Best Baking Tips for Beginners", "neutral") is True

    # --- Strong include URL signal overrides title concerns ---

    def test_strong_include_overrides_editorial_title(self):
        assert (
            looks_like_recipe_title("Google's Top Trending Recipe of 2024 Deserves a Gold Medal", "strong_include")
            is True
        )

    def test_strong_include_overrides_listicle_title(self):
        assert looks_like_recipe_title("Top 10 Things to Do in Paris", "strong_include") is True

    # --- Editorial titles with neutral URLs should FAIL ---

    def test_editorial_gold_medal_article_rejected(self):
        assert looks_like_recipe_title("Google's Top Trending Recipe of 2024 Deserves a Gold Medal", "neutral") is False

    def test_editorial_weeknight_winner_rejected(self):
        assert looks_like_recipe_title("Google's Top Trending Recipe of 2023 Is a Weeknight Winner", "neutral") is False

    def test_travel_destination_rejected(self):
        assert looks_like_recipe_title("This Southern Spot Is 2025's Most Beautiful Destination", "neutral") is False

    def test_book_travel_rejected(self):
        assert looks_like_recipe_title("This Is The Best Time to Book Thanksgiving Travel", "neutral") is False

    def test_listicle_things_to_do_rejected(self):
        assert looks_like_recipe_title("Top 10 Things to Do in New York", "neutral") is False

    def test_listicle_best_destinations_rejected(self):
        assert looks_like_recipe_title("5 Best Destinations for Food Lovers", "neutral") is False

    def test_listicle_reasons_to_visit_rejected(self):
        assert looks_like_recipe_title("7 Reasons to Visit Italy", "neutral") is False

    def test_travel_guide_rejected(self):
        assert looks_like_recipe_title("Ultimate Travel Guide to Southeast Asia", "neutral") is False

    def test_restaurant_review_rejected(self):
        assert looks_like_recipe_title("Restaurant Review: The New Italian Place Downtown", "neutral") is False

    def test_about_us_rejected(self):
        assert looks_like_recipe_title("About Us", "neutral") is False

    def test_newsletter_signup_rejected(self):
        assert looks_like_recipe_title("Subscribe to Our Newsletter", "neutral") is False

    # --- Mixed signals: title with recipe URL ---

    def test_mixed_signal_travel_recipe_with_recipe_url(self):
        """Recipe URL + travel-ish title with recipe context = PASS."""
        assert (
            looks_like_recipe_title("The Best Chicken Recipe I Found While Traveling in Morocco", "strong_include")
            is True
        )

    def test_empty_title_rejected(self):
        assert looks_like_recipe_title("", "neutral") is False

    def test_whitespace_title_rejected(self):
        assert looks_like_recipe_title("   ", "neutral") is False


