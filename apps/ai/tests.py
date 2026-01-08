"""Tests for the AI app."""

import pytest
from django.test import TestCase

from .models import AIPrompt
from .services.validator import AIResponseValidator, ValidationError


class AIPromptModelTests(TestCase):
    """Tests for the AIPrompt model."""

    def test_prompts_seeded(self):
        """Verify all 10 prompts were seeded."""
        assert AIPrompt.objects.count() == 10

    def test_all_prompt_types_exist(self):
        """Verify all prompt types are present."""
        expected_types = [
            'recipe_remix',
            'serving_adjustment',
            'tips_generation',
            'discover_favorites',
            'discover_seasonal',
            'discover_new',
            'search_ranking',
            'timer_naming',
            'remix_suggestions',
            'selector_repair',
        ]
        for prompt_type in expected_types:
            assert AIPrompt.objects.filter(prompt_type=prompt_type).exists()

    def test_get_prompt(self):
        """Test getting a prompt by type."""
        prompt = AIPrompt.get_prompt('recipe_remix')
        assert prompt.name == 'Recipe Remix'

    def test_get_prompt_not_found(self):
        """Test getting a non-existent prompt raises error."""
        with pytest.raises(AIPrompt.DoesNotExist):
            AIPrompt.get_prompt('nonexistent')

    def test_format_user_prompt(self):
        """Test formatting a user prompt template."""
        prompt = AIPrompt.get_prompt('timer_naming')
        formatted = prompt.format_user_prompt(
            instruction='Simmer for 20 minutes',
            duration='20 minutes'
        )
        assert 'Simmer for 20 minutes' in formatted
        assert '20 minutes' in formatted


class AIResponseValidatorTests(TestCase):
    """Tests for the AI response validator."""

    def setUp(self):
        self.validator = AIResponseValidator()

    def test_validate_recipe_remix_valid(self):
        """Test validating a valid recipe remix response."""
        response = {
            'title': 'Vegan Chocolate Cake',
            'description': 'A delicious plant-based cake',
            'ingredients': ['flour', 'cocoa', 'sugar'],
            'instructions': ['Mix dry ingredients', 'Add wet ingredients', 'Bake'],
        }
        result = self.validator.validate('recipe_remix', response)
        assert result == response

    def test_validate_recipe_remix_missing_field(self):
        """Test validation fails with missing required field."""
        response = {
            'title': 'Vegan Chocolate Cake',
            'description': 'A delicious plant-based cake',
            # missing ingredients and instructions
        }
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate('recipe_remix', response)
        assert 'ingredients' in str(exc_info.value.errors)

    def test_validate_tips_generation_valid(self):
        """Test validating tips generation response."""
        response = ['Tip 1', 'Tip 2', 'Tip 3']
        result = self.validator.validate('tips_generation', response)
        assert result == response

    def test_validate_tips_generation_too_few(self):
        """Test tips validation fails with too few items."""
        response = ['Tip 1', 'Tip 2']  # minItems is 3
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate('tips_generation', response)
        assert 'at least 3 items' in str(exc_info.value.errors)

    def test_validate_remix_suggestions_valid(self):
        """Test validating remix suggestions response."""
        response = ['Make it vegan', 'Add more protein', 'Use seasonal ingredients',
                    'Make it spicy', 'Make it low-carb', 'Add a crunchy topping']
        result = self.validator.validate('remix_suggestions', response)
        assert len(result) == 6

    def test_validate_remix_suggestions_wrong_count(self):
        """Test remix suggestions validation fails with wrong count."""
        response = ['Tip 1', 'Tip 2', 'Tip 3']  # Should be exactly 6
        with pytest.raises(ValidationError):
            self.validator.validate('remix_suggestions', response)

    def test_validate_timer_naming_valid(self):
        """Test validating timer naming response."""
        response = {'label': 'Simmer sauce'}
        result = self.validator.validate('timer_naming', response)
        assert result['label'] == 'Simmer sauce'

    def test_validate_search_ranking_valid(self):
        """Test validating search ranking response."""
        response = [2, 0, 4, 1, 3]
        result = self.validator.validate('search_ranking', response)
        assert result == response

    def test_validate_selector_repair_valid(self):
        """Test validating selector repair response."""
        response = {
            'suggestions': ['.recipe-title', 'h1.recipe-name'],
            'confidence': 0.85
        }
        result = self.validator.validate('selector_repair', response)
        assert result['confidence'] == 0.85

    def test_validate_unknown_prompt_type(self):
        """Test validation fails with unknown prompt type."""
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate('unknown_type', {})
        assert 'Unknown prompt type' in str(exc_info.value)

    def test_validate_wrong_type(self):
        """Test validation fails with wrong data type."""
        with pytest.raises(ValidationError):
            self.validator.validate('tips_generation', {'not': 'an array'})


class AIAPITests(TestCase):
    """Tests for the AI API endpoints."""

    def test_ai_status_endpoint(self):
        """Test the AI status endpoint."""
        response = self.client.get('/api/ai/status')
        assert response.status_code == 200
        data = response.json()
        assert 'available' in data
        assert 'default_model' in data

    def test_models_endpoint(self):
        """Test the models list endpoint."""
        response = self.client.get('/api/ai/models')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10  # 10 models defined
        assert data[0]['id'] == 'anthropic/claude-3.5-haiku'

    def test_prompts_endpoint(self):
        """Test the prompts list endpoint."""
        response = self.client.get('/api/ai/prompts')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10  # 10 prompts seeded

    def test_get_prompt_endpoint(self):
        """Test getting a specific prompt."""
        response = self.client.get('/api/ai/prompts/recipe_remix')
        assert response.status_code == 200
        data = response.json()
        assert data['prompt_type'] == 'recipe_remix'
        assert data['name'] == 'Recipe Remix'

    def test_get_prompt_not_found(self):
        """Test getting a non-existent prompt."""
        response = self.client.get('/api/ai/prompts/nonexistent')
        assert response.status_code == 404

    def test_update_prompt_endpoint(self):
        """Test updating a prompt."""
        response = self.client.put(
            '/api/ai/prompts/recipe_remix',
            data={'model': 'openai/gpt-4o'},
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.json()
        assert data['model'] == 'openai/gpt-4o'

        # Verify persistence
        prompt = AIPrompt.objects.get(prompt_type='recipe_remix')
        assert prompt.model == 'openai/gpt-4o'

    def test_test_api_key_empty(self):
        """Test API key validation with empty key."""
        response = self.client.post(
            '/api/ai/test-api-key',
            data={'api_key': ''},
            content_type='application/json'
        )
        assert response.status_code == 400
