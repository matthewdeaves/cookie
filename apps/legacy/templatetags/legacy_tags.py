"""Template tags for legacy frontend."""

import re

from django import template

register = template.Library()


@register.filter
def format_time(minutes):
    """Format minutes into a human readable time string."""
    if not minutes:
        return ""
    minutes = int(minutes)
    if minutes < 60:
        return f"{minutes} min"
    hours = minutes // 60
    mins = minutes % 60
    if mins > 0:
        return f"{hours}h {mins}m"
    return f"{hours}h"


@register.filter
def in_list(value, collection):
    """Check if a value is in a collection (set, list, or tuple)."""
    return value in collection


@register.filter
def format_nutrition_key(key):
    """Format nutrition key into human readable label.

    Converts CamelCase keys like 'CarbohydrateContent' to 'Carbohydrate'.
    Also handles snake_case like 'saturated_fat' to 'Saturated Fat'.
    """
    if not key:
        return ""

    # Remove common suffixes
    key = re.sub(r"Content$", "", key)

    # Handle snake_case (convert to spaces, then capitalize)
    if "_" in key:
        return key.replace("_", " ").title()

    # Handle CamelCase (insert space before capitals)
    # e.g., 'SaturatedFat' -> 'Saturated Fat'
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", key)

    # Capitalize first letter
    return spaced.capitalize() if spaced else ""
