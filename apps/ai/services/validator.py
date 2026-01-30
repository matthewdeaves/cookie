"""AI response schema validation using jsonschema library."""

from typing import Any

import jsonschema


class ValidationError(Exception):
    """Raised when AI response fails validation."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


# Schema definitions for each prompt type
RESPONSE_SCHEMAS = {
    "recipe_remix": {
        "type": "object",
        "required": ["title", "ingredients", "instructions", "description"],
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "ingredients": {"type": "array", "items": {"type": "string"}},
            "instructions": {"type": "array", "items": {"type": "string"}},
            "prep_time": {"type": "string"},
            "cook_time": {"type": "string"},
            "total_time": {"type": "string"},
            "yields": {"type": "string"},
        },
    },
    "serving_adjustment": {
        "type": "object",
        "required": ["ingredients"],
        "properties": {
            "ingredients": {"type": "array", "items": {"type": "string"}},
            "instructions": {"type": "array", "items": {"type": "string"}},  # QA-031
            "notes": {"type": "array", "items": {"type": "string"}},
            "prep_time": {"type": ["string", "null"]},  # QA-032
            "cook_time": {"type": ["string", "null"]},  # QA-032
            "total_time": {"type": ["string", "null"]},  # QA-032
        },
    },
    "tips_generation": {
        "type": "array",
        "items": {"type": "string"},
        "minItems": 3,
        "maxItems": 5,
    },
    "timer_naming": {
        "type": "object",
        "required": ["label"],
        "properties": {
            "label": {"type": "string"},
        },
    },
    "remix_suggestions": {
        "type": "array",
        "items": {"type": "string"},
        "minItems": 6,
        "maxItems": 6,
    },
    "discover_favorites": {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["search_query", "title", "description"],
            "properties": {
                "search_query": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
            },
        },
        "minItems": 1,
        "maxItems": 5,
    },
    "discover_seasonal": {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["search_query", "title", "description"],
            "properties": {
                "search_query": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
            },
        },
        "minItems": 1,
        "maxItems": 5,
    },
    "discover_new": {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["search_query", "title", "description"],
            "properties": {
                "search_query": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
            },
        },
        "minItems": 1,
        "maxItems": 5,
    },
    "search_ranking": {
        "type": "array",
        "items": {"type": "integer"},
    },
    "selector_repair": {
        "type": "object",
        "required": ["suggestions", "confidence"],
        "properties": {
            "suggestions": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number"},
        },
    },
    "nutrition_estimate": {
        "type": "object",
        "required": ["calories"],
        "properties": {
            "calories": {"type": "string"},
            "carbohydrateContent": {"type": "string"},
            "proteinContent": {"type": "string"},
            "fatContent": {"type": "string"},
            "saturatedFatContent": {"type": "string"},
            "unsaturatedFatContent": {"type": "string"},
            "cholesterolContent": {"type": "string"},
            "sodiumContent": {"type": "string"},
            "fiberContent": {"type": "string"},
        },
    },
}


class AIResponseValidator:
    """Validates AI responses against expected schemas using jsonschema."""

    def validate(self, prompt_type: str, response: Any) -> dict | list:
        """Validate an AI response against its expected schema.

        Args:
            prompt_type: The type of prompt (e.g., 'recipe_remix').
            response: The parsed JSON response from the AI.

        Returns:
            The validated response.

        Raises:
            ValidationError: If the response doesn't match the schema.
        """
        if prompt_type not in RESPONSE_SCHEMAS:
            raise ValidationError(f"Unknown prompt type: {prompt_type}")

        schema = RESPONSE_SCHEMAS[prompt_type]

        try:
            jsonschema.validate(response, schema)
        except jsonschema.ValidationError as e:
            # Convert jsonschema error to human-readable format
            errors = [self._format_error(e)]
            raise ValidationError(f"AI response validation failed for {prompt_type}", errors=errors)

        return response

    def _format_error(self, error: jsonschema.ValidationError) -> str:
        """Convert a jsonschema ValidationError to a human-readable message."""
        path = "response" + "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in error.absolute_path)

        # Handle different error types with user-friendly messages
        if error.validator == "required":
            # error.message is like "'ingredients' is a required property"
            # Extract the field name from the message
            import re

            match = re.search(r"'([^']+)' is a required property", error.message)
            if match:
                return f'{path}: missing required field "{match.group(1)}"'
            # Fallback: find which field is actually missing
            for field in error.validator_value:
                if field not in error.instance:
                    return f'{path}: missing required field "{field}"'
            return f"{path}: {error.message}"

        elif error.validator == "type":
            expected = error.validator_value
            if isinstance(expected, list):
                expected = " or ".join(expected)
            actual = type(error.instance).__name__
            return f"{path}: expected {expected}, got {actual}"

        elif error.validator == "minItems":
            return f"{path}: expected at least {error.validator_value} items, got {len(error.instance)}"

        elif error.validator == "maxItems":
            return f"{path}: expected at most {error.validator_value} items, got {len(error.instance)}"

        # Fallback to the default jsonschema message
        return f"{path}: {error.message}"

    def get_schema(self, prompt_type: str) -> dict | None:
        """Get the schema for a prompt type."""
        return RESPONSE_SCHEMAS.get(prompt_type)
