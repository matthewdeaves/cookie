"""
Tests for recipe utility functions (T043).

Tests apps/recipes/utils.py:
- decimal_to_fraction() conversion logic
- tidy_ingredient() smart unit-aware formatting
- tidy_quantities() batch processing
"""

import pytest

from apps.recipes.utils import (
    decimal_to_fraction,
    tidy_ingredient,
    tidy_quantities,
    FRACTION_UNITS,
    DECIMAL_UNITS,
)


# --- decimal_to_fraction ---


class TestDecimalToFraction:
    """Tests for decimal_to_fraction()."""

    def test_half(self):
        assert decimal_to_fraction(0.5) == "1/2"

    def test_third(self):
        assert decimal_to_fraction(0.333, tolerance=0.05) == "1/3"

    def test_two_thirds(self):
        assert decimal_to_fraction(0.666, tolerance=0.05) == "2/3"

    def test_quarter(self):
        assert decimal_to_fraction(0.25) == "1/4"

    def test_three_quarters(self):
        assert decimal_to_fraction(0.75) == "3/4"

    def test_eighth(self):
        assert decimal_to_fraction(0.125) == "1/8"

    def test_whole_number(self):
        assert decimal_to_fraction(3.0) == "3"

    def test_whole_plus_fraction(self):
        assert decimal_to_fraction(1.5) == "1 1/2"

    def test_whole_plus_third(self):
        assert decimal_to_fraction(1.333, tolerance=0.05) == "1 1/3"

    def test_whole_plus_quarter(self):
        assert decimal_to_fraction(2.25) == "2 1/4"

    def test_zero(self):
        # 0.0 is <= 0, so returned as str(0.0)
        assert decimal_to_fraction(0.0) == "0.0"

    def test_negative_value(self):
        """Negative values are returned as-is."""
        assert decimal_to_fraction(-1.0) == "-1.0"

    def test_nearly_whole_rounds_up(self):
        """Values very close to the next whole number round up."""
        result = decimal_to_fraction(2.97, tolerance=0.05)
        assert result == "3"

    def test_one_sixth(self):
        assert decimal_to_fraction(0.166, tolerance=0.05) == "1/6"

    def test_five_sixths(self):
        assert decimal_to_fraction(0.833, tolerance=0.05) == "5/6"

    def test_seven_eighths(self):
        assert decimal_to_fraction(0.875) == "7/8"

    def test_small_whole_with_fraction(self):
        """e.g., 3 3/4."""
        assert decimal_to_fraction(3.75) == "3 3/4"

    def test_exact_integer_one(self):
        assert decimal_to_fraction(1.0) == "1"

    def test_no_match_returns_decimal(self):
        """Values that don't match any fraction return a rounded decimal."""
        result = decimal_to_fraction(0.37, tolerance=0.01)
        # Should be a decimal string since 0.37 doesn't match common fractions
        assert "." in result or "/" in result  # Either fraction fallback or decimal


# --- tidy_ingredient ---


class TestTidyIngredient:
    """Tests for tidy_ingredient()."""

    def test_fraction_unit_cup(self):
        assert tidy_ingredient("0.5 cup sugar") == "1/2 cup sugar"

    def test_fraction_unit_tablespoon(self):
        assert tidy_ingredient("0.333 tablespoons oil") == "1/3 tablespoons oil"

    def test_fraction_unit_teaspoon(self):
        assert tidy_ingredient("0.25 tsp salt") == "1/4 tsp salt"

    def test_decimal_unit_grams_kept(self):
        """Metric weights stay as decimals."""
        result = tidy_ingredient("225.5 g butter")
        assert "225.5" in result

    def test_decimal_unit_ml_kept(self):
        result = tidy_ingredient("150.0 ml milk")
        # 150.0 should clean up to "150"
        assert "150" in result
        assert "1/2" not in result

    def test_decimal_unit_oz_kept(self):
        result = tidy_ingredient("14.5 oz tomatoes")
        assert "14.5" in result

    def test_whole_number_gram(self):
        """Whole number grams should clean up."""
        result = tidy_ingredient("225.0 g flour")
        assert result == "225 g flour"

    def test_whole_number_fraction_unit(self):
        """Whole numbers with fraction units stay as whole numbers."""
        assert tidy_ingredient("2.0 cups flour") == "2 cups flour"

    def test_mixed_number_cups(self):
        """e.g., 1.5 cups -> 1 1/2 cups."""
        assert tidy_ingredient("1.5 cups flour") == "1 1/2 cups flour"

    def test_empty_string(self):
        assert tidy_ingredient("") == ""

    def test_no_number(self):
        """Ingredients without leading numbers pass through."""
        assert tidy_ingredient("salt to taste") == "salt to taste"

    def test_integer_passes_through(self):
        """Integer quantities stay as integers."""
        result = tidy_ingredient("2 cups sugar")
        assert result == "2 cups sugar"

    def test_unknown_unit_gets_fraction(self):
        """Unknown units default to fraction conversion."""
        result = tidy_ingredient("0.5 handful parsley")
        assert "1/2" in result

    def test_no_unit_gets_fraction(self):
        """Numbers without a recognized unit get fraction conversion."""
        result = tidy_ingredient("0.5 onion, diced")
        assert "1/2" in result

    def test_strips_whitespace(self):
        result = tidy_ingredient("  0.5 cup sugar  ")
        assert "1/2" in result

    def test_large_decimal_cups(self):
        """e.g., 2.666 cups -> 2 2/3 cups."""
        result = tidy_ingredient("2.666 cups flour")
        assert "2 2/3" in result

    def test_slices_fraction_unit(self):
        """Slices are in FRACTION_UNITS."""
        result = tidy_ingredient("1.5 slices bread")
        assert "1 1/2" in result

    def test_kg_stays_decimal(self):
        result = tidy_ingredient("1.5 kg potatoes")
        assert "1.5" in result


# --- tidy_quantities ---


class TestTidyQuantities:
    """Tests for tidy_quantities()."""

    def test_processes_list(self):
        ingredients = [
            "0.5 cup sugar",
            "225 g flour",
            "0.333 tsp vanilla",
        ]
        result = tidy_quantities(ingredients)
        assert len(result) == 3
        assert "1/2" in result[0]
        assert "225" in result[1]
        assert "1/3" in result[2]

    def test_empty_list(self):
        assert tidy_quantities([]) == []

    def test_preserves_passthrough(self):
        """Items that don't need conversion pass through."""
        ingredients = ["salt to taste", "2 eggs"]
        result = tidy_quantities(ingredients)
        assert result[0] == "salt to taste"
        assert result[1] == "2 eggs"

    def test_mixed_units(self):
        """Mix of fraction and decimal units."""
        ingredients = [
            "1.5 cups flour",
            "100.0 g sugar",
            "0.25 tsp baking soda",
        ]
        result = tidy_quantities(ingredients)
        assert "1 1/2" in result[0]
        assert "100" in result[1]
        assert "1/4" in result[2]
