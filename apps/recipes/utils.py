"""Utility functions for recipe processing."""

import re
from fractions import Fraction


# Units where decimals should be converted to fractions
# These are "practical" units where fractions are more readable
FRACTION_UNITS = {
    # Volume (US customary)
    'cup', 'cups',
    'tablespoon', 'tablespoons', 'tbsp',
    'teaspoon', 'teaspoons', 'tsp',
    'pint', 'pints',
    'quart', 'quarts',
    'gallon', 'gallons',
    # Countable items (no unit or implied whole)
    'piece', 'pieces',
    'slice', 'slices',
    'clove', 'cloves',
    'sprig', 'sprigs',
    'bunch', 'bunches',
    'head', 'heads',
    'stalk', 'stalks',
    'can', 'cans',
    'package', 'packages',
    'stick', 'sticks',
}

# Units where decimals should be kept (precise measurements)
DECIMAL_UNITS = {
    # Metric weight
    'g', 'gram', 'grams',
    'kg', 'kilogram', 'kilograms',
    # Metric volume
    'ml', 'milliliter', 'milliliters',
    'l', 'liter', 'liters', 'litre', 'litres',
    # Imperial weight (often used precisely)
    'oz', 'ounce', 'ounces',
    'lb', 'lbs', 'pound', 'pounds',
}

# Common decimal to fraction mappings (tolerance-based matching)
FRACTION_MAP = [
    (1/8, '1/8'),
    (1/6, '1/6'),
    (1/4, '1/4'),
    (1/3, '1/3'),
    (3/8, '3/8'),
    (1/2, '1/2'),
    (5/8, '5/8'),
    (2/3, '2/3'),
    (3/4, '3/4'),
    (5/6, '5/6'),
    (7/8, '7/8'),
]


def decimal_to_fraction(value: float, tolerance: float = 0.05) -> str:
    """Convert a decimal to a common fraction string.

    Args:
        value: The decimal value to convert (e.g., 0.5, 1.333)
        tolerance: How close the value must be to match a fraction

    Returns:
        A string like "1/2", "1 1/3", or the original number if no match
    """
    if value <= 0:
        return str(value)

    # Split into whole and fractional parts
    whole = int(value)
    frac = value - whole

    # If it's essentially a whole number, return it
    if frac < tolerance:
        return str(whole) if whole > 0 else '0'

    # If fractional part is close to 1, round up
    if frac > (1 - tolerance):
        return str(whole + 1)

    # Find the CLOSEST matching fraction (not just first within tolerance)
    frac_str = None
    best_diff = tolerance
    for target, string in FRACTION_MAP:
        diff = abs(frac - target)
        if diff < best_diff:
            best_diff = diff
            frac_str = string

    # If no match found, try Python's Fraction with limit
    if frac_str is None:
        try:
            f = Fraction(frac).limit_denominator(8)
            if f.numerator > 0 and f.denominator <= 8:
                frac_str = f'{f.numerator}/{f.denominator}'
        except (ValueError, ZeroDivisionError):
            pass

    # Build the result
    if frac_str:
        if whole > 0:
            return f'{whole} {frac_str}'
        return frac_str

    # No fraction match - return rounded decimal
    if whole > 0:
        return f'{value:.2f}'.rstrip('0').rstrip('.')
    return f'{value:.2f}'.rstrip('0').rstrip('.')


def tidy_ingredient(ingredient: str) -> str:
    """Tidy up an ingredient string by converting decimals to fractions.

    Converts impractical decimal quantities to readable fractions for
    appropriate units (cups, tablespoons, etc.) while leaving precise
    measurements (grams, ml) as-is.

    Args:
        ingredient: An ingredient string like "0.666 cups flour"

    Returns:
        Tidied string like "2/3 cups flour"

    Examples:
        >>> tidy_ingredient("0.5 cup sugar")
        "1/2 cup sugar"
        >>> tidy_ingredient("1.333 cups flour")
        "1 1/3 cups flour"
        >>> tidy_ingredient("225g butter")
        "225g butter"  # Left as-is (metric)
    """
    if not ingredient:
        return ingredient

    # Pattern to match a number (possibly decimal) at the start or after spaces
    # Captures: (number)(optional space)(rest of string)
    pattern = r'^(\d+\.?\d*)\s*(.*)$'
    match = re.match(pattern, ingredient.strip())

    if not match:
        return ingredient

    number_str = match.group(1)
    rest = match.group(2)

    # Try to parse the number
    try:
        number = float(number_str)
    except ValueError:
        return ingredient

    # Check if this looks like a precise unit (should keep decimal)
    rest_lower = rest.lower()
    first_word = rest_lower.split()[0] if rest_lower.split() else ''

    # If it's a decimal unit, keep as-is but clean up excessive precision
    if first_word in DECIMAL_UNITS:
        # Just round to reasonable precision for display
        if number == int(number):
            return f'{int(number)} {rest}'
        return f'{number:.1f} {rest}'.replace('.0 ', ' ')

    # For fraction units or unknown units, convert to fraction
    fraction_str = decimal_to_fraction(number)

    return f'{fraction_str} {rest}'.strip()


def tidy_quantities(ingredients: list[str]) -> list[str]:
    """Tidy all ingredient quantities in a list.

    Args:
        ingredients: List of ingredient strings

    Returns:
        List with tidied quantities
    """
    return [tidy_ingredient(ing) for ing in ingredients]
