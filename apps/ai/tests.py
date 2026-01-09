"""Tests for the AI app."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase

from apps.core.models import AppSettings
from .models import AIPrompt
from .services.openrouter import (
    OpenRouterService,
    AIUnavailableError,
    AIResponseError,
)
from .services.validator import AIResponseValidator, ValidationError


class AIPromptModelTests(TestCase):
    """Tests for the AIPrompt model."""

    def test_prompts_seeded(self):
        """Verify all 11 prompts were seeded."""
        assert AIPrompt.objects.count() == 11

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
            'nutrition_estimate',
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

    def test_models_endpoint_no_api_key(self):
        """Test the models list endpoint returns empty without API key."""
        response = self.client.get('/api/ai/models')
        assert response.status_code == 200
        data = response.json()
        assert data == []  # No models without API key

    @patch('apps.ai.api.OpenRouterService')
    def test_models_endpoint_with_api_key(self, mock_service_class):
        """Test the models list endpoint returns models from OpenRouter."""
        mock_service = MagicMock()
        mock_service.get_available_models.return_value = [
            {'id': 'anthropic/claude-3.5-haiku', 'name': 'Claude 3.5 Haiku'},
            {'id': 'openai/gpt-4o', 'name': 'GPT-4o'},
        ]
        mock_service_class.return_value = mock_service

        response = self.client.get('/api/ai/models')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['id'] == 'anthropic/claude-3.5-haiku'

    def test_prompts_endpoint(self):
        """Test the prompts list endpoint."""
        response = self.client.get('/api/ai/prompts')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 11  # 11 prompts seeded

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

    @patch('apps.ai.api.OpenRouterService')
    def test_update_prompt_invalid_model(self, mock_service_class):
        """Test updating a prompt with invalid model returns 422."""
        # Mock get_available_models to return a list that doesn't include the invalid model
        mock_service = MagicMock()
        mock_service.get_available_models.return_value = [
            {'id': 'anthropic/claude-3.5-haiku', 'name': 'Claude 3.5 Haiku'},
            {'id': 'openai/gpt-4o', 'name': 'GPT-4o'},
        ]
        mock_service_class.return_value = mock_service

        response = self.client.put(
            '/api/ai/prompts/recipe_remix',
            data={'model': 'invalid/model-name'},
            content_type='application/json'
        )
        assert response.status_code == 422
        data = response.json()
        assert data['error'] == 'invalid_model'
        assert 'invalid/model-name' in data['message']

    def test_test_api_key_empty(self):
        """Test API key validation with empty key."""
        response = self.client.post(
            '/api/ai/test-api-key',
            data={'api_key': ''},
            content_type='application/json'
        )
        assert response.status_code == 400


class OpenRouterServiceTests(TestCase):
    """Tests for the OpenRouter service."""

    def test_init_requires_api_key(self):
        """Test that service requires an API key."""
        # Clear the API key from settings
        settings = AppSettings.get()
        settings.openrouter_api_key = ''
        settings.save()

        with pytest.raises(AIUnavailableError) as exc_info:
            OpenRouterService()
        assert 'not configured' in str(exc_info.value)

    def test_init_with_explicit_key(self):
        """Test initializing with an explicit API key."""
        service = OpenRouterService(api_key='test-key-123')
        assert service.api_key == 'test-key-123'

    def test_is_available_without_key(self):
        """Test is_available returns False without API key."""
        settings = AppSettings.get()
        settings.openrouter_api_key = ''
        settings.save()

        assert OpenRouterService.is_available() is False

    def test_is_available_with_key(self):
        """Test is_available returns True with API key."""
        settings = AppSettings.get()
        settings.openrouter_api_key = 'test-key-123'
        settings.save()

        assert OpenRouterService.is_available() is True

    @patch('apps.ai.services.openrouter.OpenRouter')
    def test_complete_success(self, mock_openrouter_class):
        """Test successful completion request."""
        # Setup mock
        mock_client = MagicMock()
        mock_openrouter_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_openrouter_class.return_value.__exit__ = Mock(return_value=False)

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"status": "ok"}'))]
        mock_client.chat.send.return_value = mock_response

        # Test
        service = OpenRouterService(api_key='test-key')
        result = service.complete(
            system_prompt='Test system',
            user_prompt='Test user',
            json_response=True,
        )

        assert result == {'status': 'ok'}
        mock_client.chat.send.assert_called_once()

    @patch('apps.ai.services.openrouter.OpenRouter')
    def test_complete_handles_code_block_json(self, mock_openrouter_class):
        """Test completion handles JSON wrapped in code blocks."""
        mock_client = MagicMock()
        mock_openrouter_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_openrouter_class.return_value.__exit__ = Mock(return_value=False)

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(
            content='```json\n{"title": "Test Recipe"}\n```'
        ))]
        mock_client.chat.send.return_value = mock_response

        service = OpenRouterService(api_key='test-key')
        result = service.complete(
            system_prompt='Test',
            user_prompt='Test',
            json_response=True,
        )

        assert result == {'title': 'Test Recipe'}

    @patch('apps.ai.services.openrouter.OpenRouter')
    def test_complete_invalid_json(self, mock_openrouter_class):
        """Test completion raises error for invalid JSON."""
        mock_client = MagicMock()
        mock_openrouter_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_openrouter_class.return_value.__exit__ = Mock(return_value=False)

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='not valid json'))]
        mock_client.chat.send.return_value = mock_response

        service = OpenRouterService(api_key='test-key')
        with pytest.raises(AIResponseError) as exc_info:
            service.complete(
                system_prompt='Test',
                user_prompt='Test',
                json_response=True,
            )
        assert 'Invalid JSON' in str(exc_info.value)

    @patch('apps.ai.services.openrouter.OpenRouter')
    def test_complete_no_choices(self, mock_openrouter_class):
        """Test completion raises error when no choices returned."""
        mock_client = MagicMock()
        mock_openrouter_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_openrouter_class.return_value.__exit__ = Mock(return_value=False)

        mock_response = Mock()
        mock_response.choices = []
        mock_client.chat.send.return_value = mock_response

        service = OpenRouterService(api_key='test-key')
        with pytest.raises(AIResponseError) as exc_info:
            service.complete(
                system_prompt='Test',
                user_prompt='Test',
            )
        assert 'No choices' in str(exc_info.value)

    @patch('apps.ai.services.openrouter.OpenRouter')
    def test_complete_raw_text_response(self, mock_openrouter_class):
        """Test completion with json_response=False returns raw content."""
        mock_client = MagicMock()
        mock_openrouter_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_openrouter_class.return_value.__exit__ = Mock(return_value=False)

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='Hello, world!'))]
        mock_client.chat.send.return_value = mock_response

        service = OpenRouterService(api_key='test-key')
        result = service.complete(
            system_prompt='Test',
            user_prompt='Test',
            json_response=False,
        )

        assert result == {'content': 'Hello, world!'}

    @patch('apps.ai.services.openrouter.OpenRouter')
    def test_test_connection_success(self, mock_openrouter_class):
        """Test successful connection test."""
        mock_client = MagicMock()
        mock_openrouter_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_openrouter_class.return_value.__exit__ = Mock(return_value=False)

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"status": "ok"}'))]
        mock_client.chat.send.return_value = mock_response

        success, message = OpenRouterService.test_connection('test-key')
        assert success is True
        assert message == 'Connection successful'

    def test_test_connection_no_key(self):
        """Test connection test with empty key."""
        success, message = OpenRouterService.test_connection('')
        assert success is False
        assert 'not provided' in message or 'not configured' in message

    @patch('apps.ai.services.openrouter.OpenRouter')
    def test_get_available_models_success(self, mock_openrouter_class):
        """Test getting available models from OpenRouter, sorted alphabetically."""
        mock_client = MagicMock()
        mock_openrouter_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_openrouter_class.return_value.__exit__ = Mock(return_value=False)

        # Mock response with model data in non-alphabetical order
        mock_model1 = MagicMock()
        mock_model1.id = 'openai/gpt-4o'
        mock_model1.name = 'GPT-4o'
        mock_model2 = MagicMock()
        mock_model2.id = 'anthropic/claude-3.5-haiku'
        mock_model2.name = 'Claude 3.5 Haiku'
        mock_response = Mock()
        mock_response.data = [mock_model1, mock_model2]  # GPT first, Claude second
        mock_client.models.list.return_value = mock_response

        service = OpenRouterService(api_key='test-key')
        models = service.get_available_models()

        assert len(models) == 2
        # Should be sorted alphabetically by name
        assert models[0]['name'] == 'Claude 3.5 Haiku'
        assert models[1]['name'] == 'GPT-4o'


@pytest.mark.asyncio
class OpenRouterServiceAsyncTests(TestCase):
    """Async tests for the OpenRouter service."""

    @patch('apps.ai.services.openrouter.OpenRouter')
    async def test_complete_async_success(self, mock_openrouter_class):
        """Test successful async completion request."""
        from unittest.mock import AsyncMock

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"result": "success"}'))]

        # Create a mock client with async context manager support
        mock_client = MagicMock()
        mock_client.chat.send_async = AsyncMock(return_value=mock_response)

        # Mock the async context manager
        mock_openrouter_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_openrouter_class.return_value.__aexit__ = AsyncMock(return_value=None)

        service = OpenRouterService(api_key='test-key')
        result = await service.complete_async(
            system_prompt='Test',
            user_prompt='Test',
            json_response=True,
        )

        assert result == {'result': 'success'}


class TimerNamingServiceTests(TestCase):
    """Tests for the timer naming service."""

    @patch('apps.ai.services.timer.OpenRouterService')
    def test_generate_timer_name_success(self, mock_service_class):
        """Test successful timer name generation."""
        from apps.ai.services.timer import generate_timer_name

        mock_service = MagicMock()
        mock_service.complete.return_value = {'label': 'Simmer until reduced'}
        mock_service_class.return_value = mock_service

        result = generate_timer_name('Simmer for 20 minutes until sauce is reduced', 20)

        assert result['label'] == 'Simmer until reduced'
        mock_service.complete.assert_called_once()

    @patch('apps.ai.services.timer.OpenRouterService')
    def test_generate_timer_name_truncates_long_labels(self, mock_service_class):
        """Test that long labels are truncated to 30 characters."""
        from apps.ai.services.timer import generate_timer_name

        mock_service = MagicMock()
        # Return a label longer than 30 characters
        mock_service.complete.return_value = {'label': 'This is a very long timer label that exceeds thirty characters'}
        mock_service_class.return_value = mock_service

        result = generate_timer_name('Some instruction', 15)

        # Should be truncated to 27 chars + '...'
        assert len(result['label']) == 30
        assert result['label'].endswith('...')

    @patch('apps.ai.services.timer.OpenRouterService')
    def test_generate_timer_name_formats_duration(self, mock_service_class):
        """Test that duration is formatted correctly in the prompt."""
        from apps.ai.services.timer import generate_timer_name

        mock_service = MagicMock()
        mock_service.complete.return_value = {'label': 'Bake bread'}
        mock_service_class.return_value = mock_service

        # Test with 90 minutes (1 hour 30 minutes)
        generate_timer_name('Bake until golden', 90)

        # Check that the service was called
        call_args = mock_service.complete.call_args
        user_prompt = call_args.kwargs.get('user_prompt', call_args[1].get('user_prompt', ''))
        assert '1 hour 30 minutes' in user_prompt or mock_service.complete.called


class TimerNamingAPITests(TestCase):
    """Tests for the timer naming API endpoint."""

    @patch('apps.ai.api.generate_timer_name')
    def test_timer_name_endpoint_success(self, mock_generate):
        """Test successful timer name API call."""
        mock_generate.return_value = {'label': 'Bake until golden'}

        response = self.client.post(
            '/api/ai/timer-name',
            data={'step_text': 'Bake for 25 minutes', 'duration_minutes': 25},
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.json()
        assert data['label'] == 'Bake until golden'

    def test_timer_name_endpoint_missing_step_text(self):
        """Test timer name API with missing step_text."""
        response = self.client.post(
            '/api/ai/timer-name',
            data={'step_text': '', 'duration_minutes': 10},
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.json()
        assert 'Step text is required' in data['message']

    def test_timer_name_endpoint_invalid_duration(self):
        """Test timer name API with invalid duration."""
        response = self.client.post(
            '/api/ai/timer-name',
            data={'step_text': 'Some instruction', 'duration_minutes': 0},
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.json()
        assert 'Duration must be positive' in data['message']

    @patch('apps.ai.api.generate_timer_name')
    def test_timer_name_endpoint_ai_unavailable(self, mock_generate):
        """Test timer name API when AI is unavailable."""
        mock_generate.side_effect = AIUnavailableError('No API key')

        response = self.client.post(
            '/api/ai/timer-name',
            data={'step_text': 'Simmer for 10 minutes', 'duration_minutes': 10},
            content_type='application/json'
        )

        assert response.status_code == 503
        data = response.json()
        assert data['error'] == 'ai_unavailable'
