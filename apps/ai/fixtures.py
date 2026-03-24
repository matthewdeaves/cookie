"""Realistic AI response fixtures for testing.

These fixtures represent actual AI responses including edge cases like:
- Missing optional fields
- Null values where allowed
- Various string formats
- Edge case data values
"""

# Valid responses for each prompt type
VALID_RECIPE_REMIX = {
    "title": "Vegan Thai Peanut Noodles",
    "description": "A plant-based twist on classic pad thai with creamy peanut sauce",
    "ingredients": [
        "8 oz rice noodles",
        "1/4 cup creamy peanut butter",
        "3 tbsp soy sauce",
        "2 tbsp rice vinegar",
        "1 tbsp maple syrup",
        "1 tbsp sesame oil",
        "2 cloves garlic, minced",
        "1 block extra-firm tofu, pressed and cubed",
        "2 cups shredded cabbage",
        "1 red bell pepper, sliced",
        "1/2 cup green onions, chopped",
        "1/4 cup crushed peanuts",
        "Fresh cilantro for garnish",
    ],
    "instructions": [
        "Cook rice noodles according to package directions, drain and set aside.",
        "In a small bowl, whisk together peanut butter, soy sauce, rice vinegar, maple syrup, and 2 tbsp warm water.",
        "Heat sesame oil in a large wok or skillet over medium-high heat.",
        "Add tofu cubes and cook until golden brown on all sides, about 5-7 minutes.",
        "Add garlic and cook for 30 seconds until fragrant.",
        "Add cabbage and bell pepper, stir-fry for 3-4 minutes.",
        "Add cooked noodles and peanut sauce, toss to combine.",
        "Serve topped with green onions, crushed peanuts, and cilantro.",
    ],
    "prep_time": "15 minutes",
    "cook_time": "20 minutes",
    "total_time": "35 minutes",
    "yields": "4 servings",
}

VALID_RECIPE_REMIX_MINIMAL = {
    "title": "Simple Remix",
    "description": "A simple recipe variation",
    "ingredients": ["ingredient 1", "ingredient 2"],
    "instructions": ["Step 1", "Step 2"],
}

VALID_SERVING_ADJUSTMENT = {
    "ingredients": [
        "2 cups all-purpose flour",
        "1 cup granulated sugar",
        "3/4 cup unsalted butter, softened",
        "4 large eggs",
        "1 cup whole milk",
        "2 tsp vanilla extract",
        "2 tsp baking powder",
        "1/2 tsp salt",
    ],
    "instructions": [
        "Preheat oven to 350°F (175°C). Grease and flour two 9-inch round cake pans.",
        "In a large bowl, cream together butter and sugar until light and fluffy.",
        "Beat in eggs one at a time, then stir in vanilla.",
        "Combine flour, baking powder, and salt; gradually blend into the creamed mixture.",
        "Stir in milk until batter is smooth.",
        "Pour batter into prepared pans.",
        "Bake for 30-35 minutes or until a toothpick inserted comes out clean.",
    ],
    "notes": [
        "Butter should be room temperature for best results",
        "For even layers, use a kitchen scale to divide batter equally",
    ],
    "prep_time": "20 minutes",
    "cook_time": "35 minutes",
    "total_time": "55 minutes",
}

VALID_SERVING_ADJUSTMENT_MINIMAL = {
    "ingredients": ["1 cup flour", "1/2 cup sugar"],
}

VALID_SERVING_ADJUSTMENT_WITH_NULLS = {
    "ingredients": ["2 cups rice", "1 can coconut milk", "1 tbsp curry paste"],
    "notes": ["Best served fresh"],
    "prep_time": None,
    "cook_time": "25 minutes",
    "total_time": None,
}

VALID_TIPS_GENERATION = [
    "Let the dough rest for at least 30 minutes before rolling for a more tender crust.",
    "Brush the crust with egg wash for a golden, shiny finish.",
    "Blind bake the crust with pie weights to prevent shrinking and bubbling.",
    "Allow the pie to cool completely before slicing for clean cuts.",
]

VALID_TIPS_GENERATION_MAX = [
    "Tip 1: Use room temperature ingredients",
    "Tip 2: Preheat your oven properly",
    "Tip 3: Measure ingredients accurately",
    "Tip 4: Follow the recipe order",
    "Tip 5: Let it rest before serving",
]

VALID_TIMER_NAMING = {"label": "Simmer sauce"}

VALID_REMIX_SUGGESTIONS = [
    "Make it vegan by substituting eggs with flax eggs and dairy with oat milk",
    "Add a spicy kick with jalapeños and cayenne pepper",
    "Make it gluten-free using almond flour and gluten-free baking powder",
    "Create a Mediterranean version with olive oil, feta, and sun-dried tomatoes",
    "Make it keto-friendly by replacing sugar with erythritol and flour with almond flour",
    "Add extra protein with Greek yogurt and protein powder",
]

VALID_DISCOVER_SUGGESTIONS = [
    {
        "search_query": "autumn pumpkin soup",
        "title": "Cozy Pumpkin Soup",
        "description": "A warming soup perfect for fall evenings",
    },
    {
        "search_query": "maple glazed roasted vegetables",
        "title": "Maple Roasted Root Vegetables",
        "description": "Sweet and savory side dish featuring seasonal roots",
    },
    {
        "search_query": "apple cinnamon overnight oats",
        "title": "Apple Pie Overnight Oats",
        "description": "Grab-and-go breakfast with autumn flavors",
    },
]

VALID_SEARCH_RANKING = [2, 0, 4, 1, 3]

VALID_SELECTOR_REPAIR = {
    "suggestions": [".recipe-title", "h1.recipe-name", "[data-recipe-title]"],
    "confidence": 0.85,
}

VALID_SELECTOR_REPAIR_LOW_CONFIDENCE = {
    "suggestions": [".maybe-title"],
    "confidence": 0.3,
}

VALID_NUTRITION_ESTIMATE = {
    "calories": "350 kcal",
    "carbohydrateContent": "45g",
    "proteinContent": "12g",
    "fatContent": "14g",
    "saturatedFatContent": "3g",
    "unsaturatedFatContent": "9g",
    "cholesterolContent": "25mg",
    "sodiumContent": "480mg",
    "fiberContent": "6g",
}

VALID_NUTRITION_ESTIMATE_MINIMAL = {
    "calories": "200 kcal",
}

# Edge case responses (still valid but unusual)
EDGE_CASE_EMPTY_ARRAYS = {
    "ingredients": [],
}

EDGE_CASE_LONG_STRINGS = {
    "title": "A" * 500,
    "description": "B" * 1000,
    "ingredients": ["Very long ingredient " * 20],
    "instructions": ["Step " * 100],
}

EDGE_CASE_SPECIAL_CHARACTERS = {
    "title": "Crème Brûlée with Café & Piña Colada",
    "description": "A dessert with ñ, ü, é, and 中文 characters",
    "ingredients": ["½ cup milk", "⅓ tsp vanilla", "1°C chilled cream"],
    "instructions": ["Heat to 180°F", 'Add "fresh" ingredients'],
}

EDGE_CASE_UNICODE_FRACTIONS = {
    "ingredients": ["½ cup flour", "¼ tsp salt", "⅔ cup milk", "⅛ tsp pepper"],
}

# Invalid responses for testing validation failures
INVALID_RECIPE_REMIX_MISSING_TITLE = {
    "description": "A recipe without a title",
    "ingredients": ["flour", "sugar"],
    "instructions": ["Mix", "Bake"],
}

INVALID_RECIPE_REMIX_MISSING_INGREDIENTS = {
    "title": "Incomplete Recipe",
    "description": "Missing ingredients",
    "instructions": ["Step 1"],
}

INVALID_RECIPE_REMIX_WRONG_TYPE_INGREDIENTS = {
    "title": "Bad Recipe",
    "description": "Ingredients should be array",
    "ingredients": "flour, sugar, eggs",
    "instructions": ["Mix all"],
}

INVALID_RECIPE_REMIX_WRONG_TYPE_TITLE = {
    "title": 123,
    "description": "Title should be string",
    "ingredients": ["flour"],
    "instructions": ["mix"],
}

INVALID_TIPS_TOO_FEW = ["Tip 1", "Tip 2"]

INVALID_TIPS_TOO_MANY = [
    "Tip 1",
    "Tip 2",
    "Tip 3",
    "Tip 4",
    "Tip 5",
    "Tip 6",  # Max is 5
]

INVALID_TIPS_WRONG_TYPE = {"tips": ["This should be an array, not object"]}

INVALID_TIPS_WRONG_ITEM_TYPE = ["Tip 1", "Tip 2", 123, "Tip 4"]

INVALID_REMIX_SUGGESTIONS_WRONG_COUNT = ["Suggestion 1", "Suggestion 2", "Suggestion 3"]

INVALID_TIMER_NAMING_MISSING_LABEL = {"name": "Wrong field name"}

INVALID_SEARCH_RANKING_WRONG_TYPE = [1, 2, "three", 4]

INVALID_SELECTOR_REPAIR_MISSING_CONFIDENCE = {
    "suggestions": [".selector"],
}

INVALID_SELECTOR_REPAIR_WRONG_CONFIDENCE_TYPE = {
    "suggestions": [".selector"],
    "confidence": "high",
}

INVALID_DISCOVER_MISSING_QUERY = [
    {
        "title": "Missing Query",
        "description": "No search_query field",
    }
]

INVALID_DISCOVER_WRONG_ITEM_TYPE = ["This should be an object, not a string"]

INVALID_NUTRITION_MISSING_CALORIES = {
    "proteinContent": "12g",
    "fatContent": "8g",
}

INVALID_SERVING_ADJUSTMENT_MISSING_INGREDIENTS = {
    "notes": ["Some notes"],
    "prep_time": "10 minutes",
}

INVALID_SERVING_ADJUSTMENT_WRONG_TIME_TYPE = {
    "ingredients": ["flour", "sugar"],
    "prep_time": 15,  # Should be string or null
}

# Malformed/hallucinated responses
MALFORMED_JSON_STRING = '{"title": "Incomplete'

HALLUCINATED_EXTRA_FIELDS = {
    "title": "Recipe Title",
    "description": "A recipe",
    "ingredients": ["flour"],
    "instructions": ["mix"],
    "hallucinated_field": "AI added this unexpectedly",
    "another_fake_field": ["more hallucinated data"],
}

HALLUCINATED_NUTRITION_IMPOSSIBLE = {
    "calories": "5000 kcal",  # Unrealistic for a single serving
    "proteinContent": "500g",  # Impossible protein content
    "fatContent": "-10g",  # Negative value
}

# Empty/null edge cases
EMPTY_OBJECT = {}
EMPTY_ARRAY = []
NULL_RESPONSE = None

# Boolean confusion (AI sometimes returns booleans instead of expected types)
BOOLEAN_CONFUSION = {
    "title": True,
    "description": False,
    "ingredients": True,
    "instructions": False,
}


def get_fixture(name: str):
    """Get a fixture by name.

    Args:
        name: The fixture name (matches variable names above).

    Returns:
        The fixture data.

    Raises:
        KeyError: If fixture not found.
    """
    fixtures = {
        "valid_recipe_remix": VALID_RECIPE_REMIX,
        "valid_recipe_remix_minimal": VALID_RECIPE_REMIX_MINIMAL,
        "valid_serving_adjustment": VALID_SERVING_ADJUSTMENT,
        "valid_serving_adjustment_minimal": VALID_SERVING_ADJUSTMENT_MINIMAL,
        "valid_serving_adjustment_with_nulls": VALID_SERVING_ADJUSTMENT_WITH_NULLS,
        "valid_tips_generation": VALID_TIPS_GENERATION,
        "valid_tips_generation_max": VALID_TIPS_GENERATION_MAX,
        "valid_timer_naming": VALID_TIMER_NAMING,
        "valid_remix_suggestions": VALID_REMIX_SUGGESTIONS,
        "valid_discover_suggestions": VALID_DISCOVER_SUGGESTIONS,
        "valid_search_ranking": VALID_SEARCH_RANKING,
        "valid_selector_repair": VALID_SELECTOR_REPAIR,
        "valid_selector_repair_low_confidence": VALID_SELECTOR_REPAIR_LOW_CONFIDENCE,
        "valid_nutrition_estimate": VALID_NUTRITION_ESTIMATE,
        "valid_nutrition_estimate_minimal": VALID_NUTRITION_ESTIMATE_MINIMAL,
        "invalid_recipe_remix_missing_title": INVALID_RECIPE_REMIX_MISSING_TITLE,
        "invalid_recipe_remix_missing_ingredients": INVALID_RECIPE_REMIX_MISSING_INGREDIENTS,
        "invalid_recipe_remix_wrong_type_ingredients": INVALID_RECIPE_REMIX_WRONG_TYPE_INGREDIENTS,
        "invalid_recipe_remix_wrong_type_title": INVALID_RECIPE_REMIX_WRONG_TYPE_TITLE,
        "invalid_tips_too_few": INVALID_TIPS_TOO_FEW,
        "invalid_tips_too_many": INVALID_TIPS_TOO_MANY,
        "invalid_tips_wrong_type": INVALID_TIPS_WRONG_TYPE,
        "invalid_tips_wrong_item_type": INVALID_TIPS_WRONG_ITEM_TYPE,
        "invalid_remix_suggestions_wrong_count": INVALID_REMIX_SUGGESTIONS_WRONG_COUNT,
        "invalid_timer_naming_missing_label": INVALID_TIMER_NAMING_MISSING_LABEL,
        "invalid_search_ranking_wrong_type": INVALID_SEARCH_RANKING_WRONG_TYPE,
        "invalid_selector_repair_missing_confidence": INVALID_SELECTOR_REPAIR_MISSING_CONFIDENCE,
        "invalid_selector_repair_wrong_confidence_type": INVALID_SELECTOR_REPAIR_WRONG_CONFIDENCE_TYPE,
        "invalid_discover_missing_query": INVALID_DISCOVER_MISSING_QUERY,
        "invalid_discover_wrong_item_type": INVALID_DISCOVER_WRONG_ITEM_TYPE,
        "invalid_nutrition_missing_calories": INVALID_NUTRITION_MISSING_CALORIES,
        "invalid_serving_adjustment_missing_ingredients": INVALID_SERVING_ADJUSTMENT_MISSING_INGREDIENTS,
        "invalid_serving_adjustment_wrong_time_type": INVALID_SERVING_ADJUSTMENT_WRONG_TIME_TYPE,
    }
    if name not in fixtures:
        raise KeyError(f"Fixture not found: {name}")
    return fixtures[name]
