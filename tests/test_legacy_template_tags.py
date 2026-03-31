"""Tests for Legacy template tag filters (format_time, format_nutrition_key)."""

from apps.legacy.templatetags.legacy_tags import format_time, format_nutrition_key


class TestFormatTimeFilter:
    """Tests for the format_time template filter."""

    def test_format_time_none(self):
        """format_time returns empty string for None."""
        assert format_time(None) == ""

    def test_format_time_zero(self):
        """format_time returns empty string for 0."""
        assert format_time(0) == ""

    def test_format_time_minutes_only(self):
        """format_time formats values under 60 as minutes."""
        assert format_time(45) == "45 min"

    def test_format_time_hours_and_minutes(self):
        """format_time formats values over 60 as hours and minutes."""
        assert format_time(90) == "1h 30m"

    def test_format_time_exact_hours(self):
        """format_time formats exact hours without minutes."""
        assert format_time(120) == "2h"

    def test_format_time_string_input(self):
        """format_time handles string input."""
        assert format_time("30") == "30 min"


class TestFormatNutritionKeyFilter:
    """Tests for the format_nutrition_key template filter."""

    def test_format_nutrition_key_none(self):
        """format_nutrition_key returns empty string for None."""
        assert format_nutrition_key(None) == ""

    def test_format_nutrition_key_empty(self):
        """format_nutrition_key returns empty string for empty string."""
        assert format_nutrition_key("") == ""

    def test_format_nutrition_key_removes_content_suffix(self):
        """format_nutrition_key strips 'Content' suffix."""
        assert format_nutrition_key("CalorieContent") == "Calorie"

    def test_format_nutrition_key_camel_case(self):
        """format_nutrition_key splits CamelCase."""
        assert format_nutrition_key("SaturatedFat") == "Saturated fat"

    def test_format_nutrition_key_snake_case(self):
        """format_nutrition_key converts snake_case to title case."""
        assert format_nutrition_key("saturated_fat") == "Saturated Fat"

    def test_format_nutrition_key_camel_with_content(self):
        """format_nutrition_key handles CamelCase with Content suffix."""
        assert format_nutrition_key("CarbohydrateContent") == "Carbohydrate"
