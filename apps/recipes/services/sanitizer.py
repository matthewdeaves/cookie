"""HTML sanitization for scraped recipe content.

Strips all HTML tags from recipe text fields before storage.
Defense-in-depth against stored XSS, regardless of frontend escaping.
"""

import nh3


def sanitize_recipe_data(data: dict) -> None:
    """Strip HTML tags from scraped recipe text fields in-place.

    Recipe content should be plain text. Any HTML from upstream sites
    is stripped to prevent stored XSS.
    """
    # Simple text fields: strip all HTML
    for key in (
        "title",
        "author",
        "description",
        "site_name",
        "yields",
        "category",
        "cuisine",
        "cooking_method",
        "language",
        "instructions_text",
    ):
        if isinstance(data.get(key), str):
            data[key] = nh3.clean(data[key], tags=set())

    # List of strings fields
    for key in (
        "ingredients",
        "instructions",
        "keywords",
        "dietary_restrictions",
        "equipment",
    ):
        if isinstance(data.get(key), list):
            data[key] = [nh3.clean(item, tags=set()) if isinstance(item, str) else item for item in data[key]]

    # Ingredient groups: list of dicts with "purpose" and "ingredients"
    for group in data.get("ingredient_groups", []):
        if isinstance(group.get("purpose"), str):
            group["purpose"] = nh3.clean(group["purpose"], tags=set())
        if isinstance(group.get("ingredients"), list):
            group["ingredients"] = [
                nh3.clean(item, tags=set()) if isinstance(item, str) else item for item in group["ingredients"]
            ]

    # Links: list of dicts — sanitize display text only, not URLs
    for link in data.get("links", []):
        if isinstance(link.get("text"), str):
            link["text"] = nh3.clean(link["text"], tags=set())
