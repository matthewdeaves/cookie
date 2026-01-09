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
        """Test the AI status endpoint returns enhanced status fields."""
        response = self.client.get('/api/ai/status')
        assert response.status_code == 200
        data = response.json()
        # Enhanced status fields (8B.11)
        assert 'available' in data
        assert 'configured' in data
        assert 'valid' in data
        assert 'default_model' in data
        assert 'error' in data
        assert 'error_code' in data

    def test_ai_status_no_api_key(self):
        """Test AI status shows not configured when no API key."""
        settings = AppSettings.get()
        settings.openrouter_api_key = ''
        settings.save()
        OpenRouterService.invalidate_key_cache()

        response = self.client.get('/api/ai/status')
        assert response.status_code == 200
        data = response.json()
        assert data['available'] is False
        assert data['configured'] is False
        assert data['valid'] is False
        assert data['error_code'] == 'no_api_key'
        assert 'No API key configured' in data['error']

    @patch.object(OpenRouterService, 'test_connection')
    def test_ai_status_invalid_api_key(self, mock_test_connection):
        """Test AI status shows invalid when API key fails validation."""
        mock_test_connection.return_value = (False, 'Invalid API key')

        settings = AppSettings.get()
        settings.openrouter_api_key = 'sk-or-invalid-key'
        settings.save()
        OpenRouterService.invalidate_key_cache()

        response = self.client.get('/api/ai/status')
        assert response.status_code == 200
        data = response.json()
        assert data['available'] is False
        assert data['configured'] is True
        assert data['valid'] is False
        assert data['error_code'] == 'invalid_api_key'

    @patch.object(OpenRouterService, 'test_connection')
    def test_ai_status_valid_api_key(self, mock_test_connection):
        """Test AI status shows valid when API key passes validation."""
        mock_test_connection.return_value = (True, 'Connection successful')

        settings = AppSettings.get()
        settings.openrouter_api_key = 'sk-or-valid-key'
        settings.save()
        OpenRouterService.invalidate_key_cache()

        response = self.client.get('/api/ai/status')
        assert response.status_code == 200
        data = response.json()
        assert data['available'] is True
        assert data['configured'] is True
        assert data['valid'] is True
        assert data['error'] is None
        assert data['error_code'] is None

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

    @patch.object(OpenRouterService, 'test_connection')
    def test_save_api_key_invalidates_cache(self, mock_test_connection):
        """Test that saving API key invalidates the validation cache."""
        mock_test_connection.return_value = (True, 'Connection successful')

        # Pre-populate the cache
        OpenRouterService._key_validation_cache[hash('old-key')] = (True, 0)

        response = self.client.post(
            '/api/ai/save-api-key',
            data={'api_key': 'new-key-123'},
            content_type='application/json'
        )
        assert response.status_code == 200

        # Cache should be cleared
        assert len(OpenRouterService._key_validation_cache) == 0


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

    @patch.object(OpenRouterService, 'test_connection')
    def test_validate_key_cached_caches_result(self, mock_test_connection):
        """Test that validate_key_cached caches validation results."""
        mock_test_connection.return_value = (True, 'Connection successful')
        OpenRouterService.invalidate_key_cache()

        # First call should hit the API
        is_valid1, error1 = OpenRouterService.validate_key_cached('test-key')
        assert is_valid1 is True
        assert error1 is None
        assert mock_test_connection.call_count == 1

        # Second call should use cache
        is_valid2, error2 = OpenRouterService.validate_key_cached('test-key')
        assert is_valid2 is True
        assert error2 is None
        assert mock_test_connection.call_count == 1  # Still 1, not called again

    @patch.object(OpenRouterService, 'test_connection')
    def test_validate_key_cached_caches_invalid_result(self, mock_test_connection):
        """Test that validate_key_cached caches invalid validation results."""
        mock_test_connection.return_value = (False, 'Invalid API key')
        OpenRouterService.invalidate_key_cache()

        # First call should hit the API
        is_valid1, error1 = OpenRouterService.validate_key_cached('bad-key')
        assert is_valid1 is False
        assert error1 is not None
        assert mock_test_connection.call_count == 1

        # Second call should use cache
        is_valid2, error2 = OpenRouterService.validate_key_cached('bad-key')
        assert is_valid2 is False
        assert mock_test_connection.call_count == 1  # Still 1, not called again

    def test_validate_key_cached_no_key(self):
        """Test that validate_key_cached handles missing key."""
        OpenRouterService.invalidate_key_cache()
        is_valid, error = OpenRouterService.validate_key_cached('')
        assert is_valid is False
        assert 'No API key configured' in error

    def test_invalidate_key_cache(self):
        """Test that invalidate_key_cache clears the cache."""
        OpenRouterService._key_validation_cache['test'] = (True, 0)
        assert len(OpenRouterService._key_validation_cache) > 0

        OpenRouterService.invalidate_key_cache()
        assert len(OpenRouterService._key_validation_cache) == 0

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


class SelectorRepairServiceTests(TestCase):
    """Tests for the selector repair service."""

    def setUp(self):
        from apps.recipes.models import SearchSource
        # Create a test SearchSource
        self.source = SearchSource.objects.create(
            host='test.example.com',
            name='Test Source',
            search_url_template='https://test.example.com/search?q={query}',
            result_selector='.old-selector',
            is_enabled=True,
            needs_attention=True,
            consecutive_failures=3,
        )

    @patch('apps.ai.services.selector.OpenRouterService')
    def test_repair_selector_success(self, mock_service_class):
        """Test successful selector repair."""
        from apps.ai.services.selector import repair_selector

        mock_service = MagicMock()
        mock_service.complete.return_value = {
            'suggestions': ['.recipe-card', '.result-item', 'article.recipe'],
            'confidence': 0.9
        }
        mock_service_class.return_value = mock_service

        result = repair_selector(
            source=self.source,
            html_sample='<div class="recipe-card">Test</div>',
            confidence_threshold=0.8,
            auto_update=True,
        )

        assert result['suggestions'] == ['.recipe-card', '.result-item', 'article.recipe']
        assert result['confidence'] == 0.9
        assert result['original_selector'] == '.old-selector'
        assert result['updated'] is True
        assert result['new_selector'] == '.recipe-card'

        # Verify source was updated
        self.source.refresh_from_db()
        assert self.source.result_selector == '.recipe-card'
        assert self.source.needs_attention is False

    @patch('apps.ai.services.selector.OpenRouterService')
    def test_repair_selector_low_confidence_no_update(self, mock_service_class):
        """Test selector repair with low confidence doesn't auto-update."""
        from apps.ai.services.selector import repair_selector

        mock_service = MagicMock()
        mock_service.complete.return_value = {
            'suggestions': ['.maybe-selector'],
            'confidence': 0.5
        }
        mock_service_class.return_value = mock_service

        result = repair_selector(
            source=self.source,
            html_sample='<div class="maybe-selector">Test</div>',
            confidence_threshold=0.8,
            auto_update=True,
        )

        assert result['confidence'] == 0.5
        assert result['updated'] is False
        assert result['new_selector'] is None

        # Verify source was NOT updated
        self.source.refresh_from_db()
        assert self.source.result_selector == '.old-selector'
        assert self.source.needs_attention is True

    @patch('apps.ai.services.selector.OpenRouterService')
    def test_repair_selector_auto_update_disabled(self, mock_service_class):
        """Test selector repair with auto_update=False."""
        from apps.ai.services.selector import repair_selector

        mock_service = MagicMock()
        mock_service.complete.return_value = {
            'suggestions': ['.new-selector'],
            'confidence': 0.95
        }
        mock_service_class.return_value = mock_service

        result = repair_selector(
            source=self.source,
            html_sample='<div class="new-selector">Test</div>',
            confidence_threshold=0.8,
            auto_update=False,
        )

        assert result['confidence'] == 0.95
        assert result['updated'] is False
        assert result['new_selector'] is None

        # Verify source was NOT updated
        self.source.refresh_from_db()
        assert self.source.result_selector == '.old-selector'

    @patch('apps.ai.services.selector.OpenRouterService')
    def test_repair_selector_truncates_html(self, mock_service_class):
        """Test that HTML sample is truncated to 50KB."""
        from apps.ai.services.selector import repair_selector

        mock_service = MagicMock()
        mock_service.complete.return_value = {
            'suggestions': ['.selector'],
            'confidence': 0.8
        }
        mock_service_class.return_value = mock_service

        # Create HTML larger than 50KB
        large_html = 'x' * 100000

        repair_selector(
            source=self.source,
            html_sample=large_html,
            auto_update=False,
        )

        # Verify the prompt was called with truncated HTML
        call_args = mock_service.complete.call_args
        user_prompt = call_args.kwargs.get('user_prompt', '')
        # The HTML in the prompt should be at most 50KB
        assert len(user_prompt) < 55000  # Some overhead for prompt template

    def test_get_sources_needing_attention(self):
        """Test getting sources that need attention."""
        from apps.ai.services.selector import get_sources_needing_attention
        from apps.recipes.models import SearchSource

        # Create additional test sources
        SearchSource.objects.create(
            host='healthy.example.com',
            name='Healthy Source',
            search_url_template='https://healthy.example.com/search?q={query}',
            is_enabled=True,
            needs_attention=False,  # Should NOT be included
        )
        SearchSource.objects.create(
            host='broken.example.com',
            name='Broken Source',
            search_url_template='https://broken.example.com/search?q={query}',
            is_enabled=True,
            needs_attention=True,  # Should be included
        )
        SearchSource.objects.create(
            host='disabled.example.com',
            name='Disabled Source',
            search_url_template='https://disabled.example.com/search?q={query}',
            is_enabled=False,  # Disabled, should NOT be included
            needs_attention=True,
        )

        sources = get_sources_needing_attention()
        hosts = [s.host for s in sources]

        assert 'test.example.com' in hosts
        assert 'broken.example.com' in hosts
        assert 'healthy.example.com' not in hosts
        assert 'disabled.example.com' not in hosts


class SelectorRepairAPITests(TestCase):
    """Tests for the selector repair API endpoints."""

    def setUp(self):
        from apps.recipes.models import SearchSource
        self.source = SearchSource.objects.create(
            host='test.example.com',
            name='Test Source',
            search_url_template='https://test.example.com/search?q={query}',
            result_selector='.old-selector',
            is_enabled=True,
            needs_attention=True,
            consecutive_failures=3,
        )

    @patch('apps.ai.api.repair_selector')
    def test_repair_selector_endpoint_success(self, mock_repair):
        """Test successful selector repair API call."""
        mock_repair.return_value = {
            'suggestions': ['.new-selector', '.backup-selector'],
            'confidence': 0.85,
            'original_selector': '.old-selector',
            'updated': True,
            'new_selector': '.new-selector',
        }

        response = self.client.post(
            '/api/ai/repair-selector',
            data={
                'source_id': self.source.id,
                'html_sample': '<div class="new-selector">Test</div>',
            },
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.json()
        assert data['suggestions'] == ['.new-selector', '.backup-selector']
        assert data['confidence'] == 0.85
        assert data['updated'] is True
        assert data['new_selector'] == '.new-selector'

    def test_repair_selector_endpoint_source_not_found(self):
        """Test repair selector API with non-existent source."""
        response = self.client.post(
            '/api/ai/repair-selector',
            data={
                'source_id': 99999,
                'html_sample': '<div>Test</div>',
            },
            content_type='application/json'
        )

        assert response.status_code == 404
        data = response.json()
        assert data['error'] == 'not_found'

    def test_repair_selector_endpoint_empty_html(self):
        """Test repair selector API with empty HTML sample."""
        response = self.client.post(
            '/api/ai/repair-selector',
            data={
                'source_id': self.source.id,
                'html_sample': '',
            },
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.json()
        assert 'HTML sample is required' in data['message']

    @patch('apps.ai.api.repair_selector')
    def test_repair_selector_endpoint_ai_unavailable(self, mock_repair):
        """Test repair selector API when AI is unavailable."""
        mock_repair.side_effect = AIUnavailableError('No API key')

        response = self.client.post(
            '/api/ai/repair-selector',
            data={
                'source_id': self.source.id,
                'html_sample': '<div>Test</div>',
            },
            content_type='application/json'
        )

        assert response.status_code == 503
        data = response.json()
        assert data['error'] == 'ai_unavailable'

    @patch('apps.ai.api.repair_selector')
    def test_repair_selector_endpoint_with_options(self, mock_repair):
        """Test repair selector API with custom options."""
        mock_repair.return_value = {
            'suggestions': ['.custom-selector'],
            'confidence': 0.7,
            'original_selector': '.old-selector',
            'updated': False,
            'new_selector': None,
        }

        response = self.client.post(
            '/api/ai/repair-selector',
            data={
                'source_id': self.source.id,
                'html_sample': '<div class="custom-selector">Test</div>',
                'target': 'recipe card element',
                'confidence_threshold': 0.9,
                'auto_update': False,
            },
            content_type='application/json'
        )

        assert response.status_code == 200
        # Verify the custom options were passed
        mock_repair.assert_called_once()
        call_kwargs = mock_repair.call_args.kwargs
        assert call_kwargs['target'] == 'recipe card element'
        assert call_kwargs['confidence_threshold'] == 0.9
        assert call_kwargs['auto_update'] is False

    def test_sources_needing_attention_endpoint(self):
        """Test the sources needing attention list endpoint."""
        response = self.client.get('/api/ai/sources-needing-attention')

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1  # At least our test source

        # Find our test source
        test_source = next((s for s in data if s['host'] == 'test.example.com'), None)
        assert test_source is not None
        assert test_source['name'] == 'Test Source'
        assert test_source['result_selector'] == '.old-selector'
        assert test_source['consecutive_failures'] == 3

    def test_sources_needing_attention_endpoint_empty(self):
        """Test sources needing attention endpoint when none exist."""
        from apps.recipes.models import SearchSource
        # Clear the needs_attention flag on our test source
        self.source.needs_attention = False
        self.source.save()
        # Clear all sources with needs_attention
        SearchSource.objects.update(needs_attention=False)

        response = self.client.get('/api/ai/sources-needing-attention')

        assert response.status_code == 200
        data = response.json()
        assert data == []


class AIFeatureFallbackTests(TestCase):
    """Tests for AI feature fallback behavior when AI is unavailable."""

    def setUp(self):
        from apps.profiles.models import Profile
        from apps.recipes.models import Recipe
        self.profile = Profile.objects.create(name='Test Profile')
        self.recipe = Recipe.objects.create(
            title='Test Recipe',
            profile=self.profile,
            ingredients=['1 cup flour', '2 eggs'],
            instructions=[{'text': 'Mix ingredients'}],
            servings=4,
        )
        # Set session profile
        session = self.client.session
        session['profile_id'] = self.profile.id
        session.save()

    def test_ai_status_shows_unavailable_without_key(self):
        """Test AI status endpoint shows unavailable when no API key."""
        settings = AppSettings.get()
        settings.openrouter_api_key = ''
        settings.save()
        OpenRouterService.invalidate_key_cache()

        response = self.client.get('/api/ai/status')
        assert response.status_code == 200
        data = response.json()
        assert data['available'] is False
        assert data['configured'] is False

    @patch.object(OpenRouterService, 'test_connection')
    def test_ai_status_shows_available_with_key(self, mock_test_connection):
        """Test AI status endpoint shows available with valid API key."""
        mock_test_connection.return_value = (True, 'Connection successful')
        settings = AppSettings.get()
        settings.openrouter_api_key = 'test-key-123'
        settings.save()
        OpenRouterService.invalidate_key_cache()

        response = self.client.get('/api/ai/status')
        assert response.status_code == 200
        data = response.json()
        assert data['available'] is True
        assert data['configured'] is True
        assert data['valid'] is True

    @patch('apps.ai.api.generate_tips')
    def test_tips_returns_503_with_action_field_when_ai_unavailable(self, mock_generate):
        """Test tips endpoint returns 503 with action field when AI is unavailable."""
        mock_generate.side_effect = AIUnavailableError('No API key')

        response = self.client.post(
            '/api/ai/tips',
            data={'recipe_id': self.recipe.id},
            content_type='application/json'
        )

        assert response.status_code == 503
        data = response.json()
        assert data['error'] == 'ai_unavailable'
        assert data['action'] == 'configure_key'
        assert 'message' in data

    @patch('apps.ai.api.get_remix_suggestions')
    def test_remix_suggestions_returns_503_when_ai_unavailable(self, mock_suggestions):
        """Test remix suggestions endpoint returns 503 when AI is unavailable."""
        mock_suggestions.side_effect = AIUnavailableError('No API key')

        response = self.client.post(
            '/api/ai/remix-suggestions',
            data={'recipe_id': self.recipe.id},
            content_type='application/json'
        )

        assert response.status_code == 503
        data = response.json()
        assert data['error'] == 'ai_unavailable'

    @patch('apps.ai.api.scale_recipe')
    def test_scale_returns_503_when_ai_unavailable(self, mock_scale):
        """Test scale endpoint returns 503 when AI is unavailable."""
        mock_scale.side_effect = AIUnavailableError('No API key')

        response = self.client.post(
            '/api/ai/scale',
            data={
                'recipe_id': self.recipe.id,
                'target_servings': 8,
                'profile_id': self.profile.id,
            },
            content_type='application/json'
        )

        assert response.status_code == 503
        data = response.json()
        assert data['error'] == 'ai_unavailable'

    @patch('apps.ai.api.get_discover_suggestions')
    def test_discover_returns_503_when_ai_unavailable(self, mock_discover):
        """Test discover endpoint returns 503 when AI is unavailable."""
        mock_discover.side_effect = AIUnavailableError('No API key')

        response = self.client.get(f'/api/ai/discover/{self.profile.id}/')

        assert response.status_code == 503
        data = response.json()
        assert data['error'] == 'ai_unavailable'

    @patch('apps.ai.services.tips.OpenRouterService')
    def test_tips_service_raises_when_no_key(self, mock_service_class):
        """Test tips service raises AIUnavailableError when no API key."""
        from apps.ai.services.tips import generate_tips
        mock_service_class.side_effect = AIUnavailableError('No API key configured')

        with pytest.raises(AIUnavailableError):
            generate_tips(self.recipe.id)

    @patch('apps.ai.services.remix.OpenRouterService')
    def test_remix_service_raises_when_no_key(self, mock_service_class):
        """Test remix service raises AIUnavailableError when no API key."""
        from apps.ai.services.remix import get_remix_suggestions
        mock_service_class.side_effect = AIUnavailableError('No API key configured')

        with pytest.raises(AIUnavailableError):
            get_remix_suggestions(self.recipe.id)

    def test_models_endpoint_returns_empty_list_without_key(self):
        """Test models endpoint returns empty list when AI unavailable."""
        settings = AppSettings.get()
        settings.openrouter_api_key = ''
        settings.save()

        response = self.client.get('/api/ai/models')
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @patch('apps.ai.api.generate_timer_name')
    def test_timer_name_returns_503_when_ai_unavailable(self, mock_generate):
        """Test timer name endpoint returns 503 when AI is unavailable."""
        mock_generate.side_effect = AIUnavailableError('No API key')

        response = self.client.post(
            '/api/ai/timer-name',
            data={'step_text': 'Bake for 25 minutes', 'duration_minutes': 25},
            content_type='application/json'
        )

        assert response.status_code == 503
        data = response.json()
        assert data['error'] == 'ai_unavailable'


class AIResponseErrorTests(TestCase):
    """Tests for AI response error handling."""

    def setUp(self):
        from apps.profiles.models import Profile
        from apps.recipes.models import Recipe
        self.profile = Profile.objects.create(name='Test Profile')
        self.recipe = Recipe.objects.create(
            title='Test Recipe',
            profile=self.profile,
            ingredients=['1 cup flour'],
            instructions=[{'text': 'Mix'}],
        )
        session = self.client.session
        session['profile_id'] = self.profile.id
        session.save()

    @patch('apps.ai.api.generate_tips')
    def test_tips_returns_400_on_ai_error(self, mock_generate):
        """Test tips endpoint returns 400 on AI response error."""
        mock_generate.side_effect = AIResponseError('Invalid JSON response')

        response = self.client.post(
            '/api/ai/tips',
            data={'recipe_id': self.recipe.id},
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.json()
        assert data['error'] == 'ai_error'

    @patch('apps.ai.api.generate_tips')
    def test_tips_returns_400_on_validation_error(self, mock_generate):
        """Test tips endpoint returns 400 on validation error."""
        mock_generate.side_effect = ValidationError('Response validation failed')

        response = self.client.post(
            '/api/ai/tips',
            data={'recipe_id': self.recipe.id},
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.json()
        assert data['error'] == 'ai_error'

    @patch('apps.ai.api.create_remix')
    def test_remix_returns_400_on_ai_error(self, mock_remix):
        """Test remix endpoint returns 400 on AI response error."""
        mock_remix.side_effect = AIResponseError('AI returned invalid data')

        response = self.client.post(
            '/api/ai/remix',
            data={
                'recipe_id': self.recipe.id,
                'modification': 'Make it vegan',
                'profile_id': self.profile.id,
            },
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.json()
        assert data['error'] == 'ai_error'

    @patch('apps.ai.api.repair_selector')
    def test_repair_selector_returns_400_on_validation_error(self, mock_repair):
        """Test repair selector endpoint returns 400 on validation error."""
        from apps.recipes.models import SearchSource
        source = SearchSource.objects.create(
            host='test.example.com',
            name='Test',
            search_url_template='https://test.example.com/search?q={query}',
        )
        mock_repair.side_effect = ValidationError('Invalid AI response schema')

        response = self.client.post(
            '/api/ai/repair-selector',
            data={
                'source_id': source.id,
                'html_sample': '<div>Test</div>',
            },
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.json()
        assert data['error'] == 'ai_error'
