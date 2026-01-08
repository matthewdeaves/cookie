"""AI response schema validation."""

from typing import Any


class ValidationError(Exception):
    """Raised when AI response fails validation."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


# Schema definitions for each prompt type
RESPONSE_SCHEMAS = {
    'recipe_remix': {
        'type': 'object',
        'required': ['title', 'ingredients', 'instructions', 'description'],
        'properties': {
            'title': {'type': 'string'},
            'description': {'type': 'string'},
            'ingredients': {'type': 'array', 'items': {'type': 'string'}},
            'instructions': {'type': 'array', 'items': {'type': 'string'}},
            'prep_time': {'type': 'string'},
            'cook_time': {'type': 'string'},
            'total_time': {'type': 'string'},
            'yields': {'type': 'string'},
        },
    },
    'serving_adjustment': {
        'type': 'object',
        'required': ['ingredients'],
        'properties': {
            'ingredients': {'type': 'array', 'items': {'type': 'string'}},
        },
    },
    'tips_generation': {
        'type': 'array',
        'items': {'type': 'string'},
        'minItems': 3,
        'maxItems': 5,
    },
    'timer_naming': {
        'type': 'object',
        'required': ['label'],
        'properties': {
            'label': {'type': 'string'},
        },
    },
    'remix_suggestions': {
        'type': 'array',
        'items': {'type': 'string'},
        'minItems': 6,
        'maxItems': 6,
    },
    'discover_favorites': {
        'type': 'object',
        'required': ['search_query', 'title', 'description'],
        'properties': {
            'search_query': {'type': 'string'},
            'title': {'type': 'string'},
            'description': {'type': 'string'},
        },
    },
    'discover_seasonal': {
        'type': 'object',
        'required': ['search_query', 'title', 'description'],
        'properties': {
            'search_query': {'type': 'string'},
            'title': {'type': 'string'},
            'description': {'type': 'string'},
        },
    },
    'discover_new': {
        'type': 'object',
        'required': ['search_query', 'title', 'description'],
        'properties': {
            'search_query': {'type': 'string'},
            'title': {'type': 'string'},
            'description': {'type': 'string'},
        },
    },
    'search_ranking': {
        'type': 'array',
        'items': {'type': 'integer'},
    },
    'selector_repair': {
        'type': 'object',
        'required': ['suggestions', 'confidence'],
        'properties': {
            'suggestions': {'type': 'array', 'items': {'type': 'string'}},
            'confidence': {'type': 'number'},
        },
    },
    'nutrition_estimate': {
        'type': 'object',
        'required': ['calories'],
        'properties': {
            'calories': {'type': 'string'},
            'carbohydrateContent': {'type': 'string'},
            'proteinContent': {'type': 'string'},
            'fatContent': {'type': 'string'},
            'saturatedFatContent': {'type': 'string'},
            'unsaturatedFatContent': {'type': 'string'},
            'cholesterolContent': {'type': 'string'},
            'sodiumContent': {'type': 'string'},
            'fiberContent': {'type': 'string'},
        },
    },
}


class AIResponseValidator:
    """Validates AI responses against expected schemas."""

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
            raise ValidationError(f'Unknown prompt type: {prompt_type}')

        schema = RESPONSE_SCHEMAS[prompt_type]
        errors = self._validate_value(response, schema, 'response')

        if errors:
            raise ValidationError(
                f'AI response validation failed for {prompt_type}',
                errors=errors
            )

        return response

    def _validate_value(
        self,
        value: Any,
        schema: dict,
        path: str
    ) -> list[str]:
        """Validate a value against a schema definition.

        Returns a list of error messages.
        """
        errors = []
        expected_type = schema.get('type')

        # Type validation
        if expected_type == 'object':
            if not isinstance(value, dict):
                return [f'{path}: expected object, got {type(value).__name__}']

            # Check required fields
            required = schema.get('required', [])
            for field in required:
                if field not in value:
                    errors.append(f'{path}: missing required field "{field}"')

            # Validate properties if defined
            properties = schema.get('properties', {})
            for key, val in value.items():
                if key in properties:
                    errors.extend(
                        self._validate_value(val, properties[key], f'{path}.{key}')
                    )

        elif expected_type == 'array':
            if not isinstance(value, list):
                return [f'{path}: expected array, got {type(value).__name__}']

            # Check array length constraints
            min_items = schema.get('minItems')
            max_items = schema.get('maxItems')

            if min_items is not None and len(value) < min_items:
                errors.append(
                    f'{path}: expected at least {min_items} items, got {len(value)}'
                )
            if max_items is not None and len(value) > max_items:
                errors.append(
                    f'{path}: expected at most {max_items} items, got {len(value)}'
                )

            # Validate items
            items_schema = schema.get('items')
            if items_schema:
                for i, item in enumerate(value):
                    errors.extend(
                        self._validate_value(item, items_schema, f'{path}[{i}]')
                    )

        elif expected_type == 'string':
            if not isinstance(value, str):
                errors.append(f'{path}: expected string, got {type(value).__name__}')

        elif expected_type == 'integer':
            if not isinstance(value, int) or isinstance(value, bool):
                errors.append(f'{path}: expected integer, got {type(value).__name__}')

        elif expected_type == 'number':
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f'{path}: expected number, got {type(value).__name__}')

        elif expected_type == 'boolean':
            if not isinstance(value, bool):
                errors.append(f'{path}: expected boolean, got {type(value).__name__}')

        return errors

    def get_schema(self, prompt_type: str) -> dict | None:
        """Get the schema for a prompt type."""
        return RESPONSE_SCHEMAS.get(prompt_type)
