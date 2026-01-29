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


# =============================================================================
# Additional AI Service Tests (Phase 2 Code Quality)
# =============================================================================

from apps.ai import fixtures


class ValidatorEdgeCaseTests(TestCase):
    """Tests for validator edge cases and _validate_value coverage."""

    def setUp(self):
        self.validator = AIResponseValidator()

    def test_validate_union_type_null(self):
        """Test validation of union type accepting null."""
        response = {
            'ingredients': ['1 cup flour'],
            'prep_time': None,  # Union type ['string', 'null']
        }
        result = self.validator.validate('serving_adjustment', response)
        assert result['prep_time'] is None

    def test_validate_union_type_string(self):
        """Test validation of union type accepting string."""
        response = fixtures.VALID_SERVING_ADJUSTMENT_WITH_NULLS
        result = self.validator.validate('serving_adjustment', response)
        assert result['cook_time'] == '25 minutes'

    def test_validate_union_type_wrong_type(self):
        """Test validation fails for union type with wrong value."""
        response = {
            'ingredients': ['flour'],
            'prep_time': 15,  # Should be string or null, not int
        }
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate('serving_adjustment', response)
        assert 'string or null' in str(exc_info.value.errors)

    def test_validate_nested_object_in_array(self):
        """Test validation of nested objects in array."""
        result = self.validator.validate('discover_seasonal', fixtures.VALID_DISCOVER_SUGGESTIONS)
        assert len(result) == 3
        assert result[0]['title'] == 'Cozy Pumpkin Soup'

    def test_validate_nested_object_missing_field(self):
        """Test validation fails for nested object missing required field."""
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate('discover_seasonal', fixtures.INVALID_DISCOVER_MISSING_QUERY)
        assert 'search_query' in str(exc_info.value.errors)

    def test_validate_number_type(self):
        """Test validation of number type (int or float)."""
        result = self.validator.validate('selector_repair', {
            'suggestions': ['.test'],
            'confidence': 0.85,
        })
        assert result['confidence'] == 0.85

    def test_validate_number_type_as_int(self):
        """Test validation accepts integer for number type."""
        result = self.validator.validate('selector_repair', {
            'suggestions': ['.test'],
            'confidence': 1,
        })
        assert result['confidence'] == 1

    def test_validate_integer_type(self):
        """Test validation of integer type."""
        result = self.validator.validate('search_ranking', [1, 2, 3])
        assert result == [1, 2, 3]

    def test_validate_integer_rejects_float(self):
        """Test integer validation rejects float values."""
        with pytest.raises(ValidationError):
            self.validator.validate('search_ranking', [1.5, 2, 3])

    def test_validate_integer_rejects_boolean(self):
        """Test integer validation rejects boolean (even though bool is int subclass)."""
        with pytest.raises(ValidationError):
            self.validator.validate('search_ranking', [True, False, 1])

    def test_validate_array_max_items(self):
        """Test validation fails when array exceeds maxItems."""
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate('tips_generation', fixtures.INVALID_TIPS_TOO_MANY)
        assert 'at most 5' in str(exc_info.value.errors)

    def test_validate_array_min_items(self):
        """Test validation fails when array has fewer than minItems."""
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate('tips_generation', fixtures.INVALID_TIPS_TOO_FEW)
        assert 'at least 3' in str(exc_info.value.errors)

    def test_validate_array_item_wrong_type(self):
        """Test validation fails when array item has wrong type."""
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate('tips_generation', fixtures.INVALID_TIPS_WRONG_ITEM_TYPE)
        assert 'expected string' in str(exc_info.value.errors)

    def test_validate_with_extra_fields_passes(self):
        """Test that extra fields are allowed (no additionalProperties: false)."""
        result = self.validator.validate('recipe_remix', fixtures.HALLUCINATED_EXTRA_FIELDS)
        assert result['title'] == 'Recipe Title'
        assert 'hallucinated_field' in result

    def test_validate_special_characters(self):
        """Test validation handles special characters correctly."""
        result = self.validator.validate('recipe_remix', fixtures.EDGE_CASE_SPECIAL_CHARACTERS)
        assert 'Crème Brûlée' in result['title']
        assert '½ cup' in result['ingredients'][0]

    def test_get_schema_returns_schema(self):
        """Test get_schema returns correct schema."""
        schema = self.validator.get_schema('recipe_remix')
        assert schema is not None
        assert schema['type'] == 'object'
        assert 'title' in schema['required']

    def test_get_schema_returns_none_for_unknown(self):
        """Test get_schema returns None for unknown type."""
        schema = self.validator.get_schema('nonexistent')
        assert schema is None


class ScalingServiceTests(TestCase):
    """Tests for the recipe scaling service."""

    def test_parse_time_minutes(self):
        """Test parsing time string with minutes."""
        from apps.ai.services.scaling import _parse_time
        assert _parse_time('30 minutes') == 30
        assert _parse_time('15 mins') == 15
        assert _parse_time('45 min') == 45

    def test_parse_time_hours(self):
        """Test parsing time string with hours."""
        from apps.ai.services.scaling import _parse_time
        assert _parse_time('1 hour') == 60
        assert _parse_time('2 hours') == 120

    def test_parse_time_hours_and_minutes(self):
        """Test parsing time string with hours and minutes."""
        from apps.ai.services.scaling import _parse_time
        assert _parse_time('1 hour 30 minutes') == 90
        assert _parse_time('2 hours 15 mins') == 135

    def test_parse_time_none(self):
        """Test parsing None returns None."""
        from apps.ai.services.scaling import _parse_time
        assert _parse_time(None) is None
        assert _parse_time('') is None

    def test_parse_time_no_numbers(self):
        """Test parsing string without numbers returns None."""
        from apps.ai.services.scaling import _parse_time
        assert _parse_time('some time') is None

    def test_format_time_minutes(self):
        """Test formatting minutes to readable string."""
        from apps.ai.services.scaling import _format_time
        assert _format_time(30) == '30 minutes'
        assert _format_time(1) == '1 minutes'

    def test_format_time_hours(self):
        """Test formatting hours to readable string."""
        from apps.ai.services.scaling import _format_time
        assert _format_time(60) == '1 hour'
        assert _format_time(120) == '2 hours'

    def test_format_time_hours_and_minutes(self):
        """Test formatting hours and minutes to readable string."""
        from apps.ai.services.scaling import _format_time
        assert _format_time(90) == '1 hour 30 minutes'
        assert _format_time(75) == '1 hour 15 minutes'

    def test_format_time_none(self):
        """Test formatting None returns 'Not specified'."""
        from apps.ai.services.scaling import _format_time
        assert _format_time(None) == 'Not specified'
        assert _format_time(0) == 'Not specified'

    def test_calculate_nutrition_empty(self):
        """Test nutrition calculation with empty nutrition data."""
        from apps.ai.services.scaling import calculate_nutrition
        from apps.recipes.models import Recipe
        from apps.profiles.models import Profile

        profile = Profile.objects.create(name='Test')
        recipe = Recipe.objects.create(
            profile=profile,
            title='Test',
            ingredients=['flour'],
            nutrition={},  # Empty dict, not None
        )

        result = calculate_nutrition(recipe, 4, 8)
        assert result == {'per_serving': {}, 'total': {}}

    def test_calculate_nutrition_string_values(self):
        """Test nutrition calculation with string values."""
        from apps.ai.services.scaling import calculate_nutrition
        from apps.recipes.models import Recipe
        from apps.profiles.models import Profile

        profile = Profile.objects.create(name='Test')
        recipe = Recipe.objects.create(
            profile=profile,
            title='Test',
            ingredients=['flour'],
            nutrition={'calories': '200 kcal', 'protein': '10 g'},
            servings=4,
        )

        result = calculate_nutrition(recipe, 4, 2)
        assert result['per_serving'] == {'calories': '200 kcal', 'protein': '10 g'}
        assert result['total']['calories'] == '400 kcal'
        assert result['total']['protein'] == '20 g'

    def test_calculate_nutrition_numeric_values(self):
        """Test nutrition calculation with numeric values."""
        from apps.ai.services.scaling import calculate_nutrition
        from apps.recipes.models import Recipe
        from apps.profiles.models import Profile

        profile = Profile.objects.create(name='Test')
        recipe = Recipe.objects.create(
            profile=profile,
            title='Test',
            ingredients=['flour'],
            nutrition={'calories': 200, 'protein': 10},
            servings=4,
        )

        result = calculate_nutrition(recipe, 4, 2)
        assert result['total']['calories'] == 400
        assert result['total']['protein'] == 20


class RemixServiceTests(TestCase):
    """Tests for the recipe remix service."""

    def test_parse_time_remix(self):
        """Test _parse_time function in remix module."""
        from apps.ai.services.remix import _parse_time
        assert _parse_time('25 minutes') == 25
        assert _parse_time('1 hour') == 60
        assert _parse_time('1 hour 15 minutes') == 75
        assert _parse_time(None) is None
        assert _parse_time('') is None
        assert _parse_time('quick') is None

    def test_parse_servings(self):
        """Test _parse_servings function."""
        from apps.ai.services.remix import _parse_servings
        assert _parse_servings('4 servings') == 4
        assert _parse_servings('Makes 6') == 6
        assert _parse_servings('12 portions') == 12
        assert _parse_servings(None) is None
        assert _parse_servings('') is None
        assert _parse_servings('many') is None

    @patch('apps.ai.services.remix.OpenRouterService')
    def test_get_remix_suggestions_success(self, mock_service_class):
        """Test get_remix_suggestions returns validated suggestions."""
        from apps.ai.services.remix import get_remix_suggestions
        from apps.recipes.models import Recipe
        from apps.profiles.models import Profile

        mock_service = MagicMock()
        mock_service.complete.return_value = fixtures.VALID_REMIX_SUGGESTIONS
        mock_service_class.return_value = mock_service

        profile = Profile.objects.create(name='Test')
        recipe = Recipe.objects.create(
            profile=profile,
            title='Chocolate Cake',
            ingredients=['flour', 'sugar', 'cocoa'],
        )

        result = get_remix_suggestions(recipe.id)
        assert len(result) == 6
        assert 'vegan' in result[0].lower()

    @patch('apps.ai.services.remix.OpenRouterService')
    def test_get_remix_suggestions_validation_error(self, mock_service_class):
        """Test get_remix_suggestions raises ValidationError on invalid response."""
        from apps.ai.services.remix import get_remix_suggestions
        from apps.recipes.models import Recipe
        from apps.profiles.models import Profile

        mock_service = MagicMock()
        mock_service.complete.return_value = ['only', 'three', 'items']
        mock_service_class.return_value = mock_service

        profile = Profile.objects.create(name='Test')
        recipe = Recipe.objects.create(
            profile=profile,
            title='Test',
            ingredients=['flour'],
        )

        with pytest.raises(ValidationError):
            get_remix_suggestions(recipe.id)


class DiscoverServiceTests(TestCase):
    """Tests for the AI discovery suggestions service."""

    def test_get_season_winter(self):
        """Test _get_season returns winter for Dec/Jan/Feb."""
        from apps.ai.services.discover import _get_season
        from datetime import datetime
        assert _get_season(datetime(2024, 12, 15)) == 'winter'
        assert _get_season(datetime(2024, 1, 15)) == 'winter'
        assert _get_season(datetime(2024, 2, 15)) == 'winter'

    def test_get_season_spring(self):
        """Test _get_season returns spring for Mar/Apr/May."""
        from apps.ai.services.discover import _get_season
        from datetime import datetime
        assert _get_season(datetime(2024, 3, 15)) == 'spring'
        assert _get_season(datetime(2024, 4, 15)) == 'spring'
        assert _get_season(datetime(2024, 5, 15)) == 'spring'

    def test_get_season_summer(self):
        """Test _get_season returns summer for Jun/Jul/Aug."""
        from apps.ai.services.discover import _get_season
        from datetime import datetime
        assert _get_season(datetime(2024, 6, 15)) == 'summer'
        assert _get_season(datetime(2024, 7, 15)) == 'summer'
        assert _get_season(datetime(2024, 8, 15)) == 'summer'

    def test_get_season_autumn(self):
        """Test _get_season returns autumn for Sep/Oct/Nov."""
        from apps.ai.services.discover import _get_season
        from datetime import datetime
        assert _get_season(datetime(2024, 9, 15)) == 'autumn'
        assert _get_season(datetime(2024, 10, 15)) == 'autumn'
        assert _get_season(datetime(2024, 11, 15)) == 'autumn'

    def test_format_suggestions_from_list(self):
        """Test _format_suggestions handles list input."""
        from apps.ai.services.discover import _format_suggestions
        from apps.ai.models import AIDiscoverySuggestion
        from apps.profiles.models import Profile

        profile = Profile.objects.create(name='Test')
        suggestion = AIDiscoverySuggestion.objects.create(
            profile=profile,
            suggestion_type='seasonal',
            search_query='pumpkin soup',
            title='Autumn Soup',
            description='Warm and cozy',
        )

        result = _format_suggestions([suggestion])
        assert len(result['suggestions']) == 1
        assert result['suggestions'][0]['type'] == 'seasonal'
        assert result['suggestions'][0]['title'] == 'Autumn Soup'
        assert 'refreshed_at' in result


class RankingServiceTests(TestCase):
    """Tests for the AI ranking service."""

    def test_is_ranking_available_no_key(self):
        """Test is_ranking_available returns False without API key."""
        from apps.ai.services.ranking import is_ranking_available
        settings = AppSettings.get()
        settings.openrouter_api_key = ''
        settings.save()
        assert is_ranking_available() is False

    def test_is_ranking_available_with_key(self):
        """Test is_ranking_available returns True with API key."""
        from apps.ai.services.ranking import is_ranking_available
        settings = AppSettings.get()
        settings.openrouter_api_key = 'test-key'
        settings.save()
        assert is_ranking_available() is True

    def test_filter_valid_removes_titleless(self):
        """Test _filter_valid removes results without titles."""
        from apps.ai.services.ranking import _filter_valid
        results = [
            {'title': 'Good Recipe', 'url': 'http://test.com/1'},
            {'url': 'http://test.com/2'},  # No title
            {'title': '', 'url': 'http://test.com/3'},  # Empty title
            {'title': 'Another Good', 'url': 'http://test.com/4'},
        ]
        filtered = _filter_valid(results)
        assert len(filtered) == 2
        assert filtered[0]['title'] == 'Good Recipe'
        assert filtered[1]['title'] == 'Another Good'

    def test_sort_by_image_prioritizes_images(self):
        """Test _sort_by_image puts results with images first."""
        from apps.ai.services.ranking import _sort_by_image
        results = [
            {'title': 'No Image', 'url': 'http://test.com/1'},
            {'title': 'Has Image', 'url': 'http://test.com/2', 'image_url': 'http://img.com/2.jpg'},
            {'title': 'Also No Image', 'url': 'http://test.com/3'},
        ]
        sorted_results = _sort_by_image(results)
        assert sorted_results[0]['title'] == 'Has Image'

    def test_sort_by_image_filters_invalid(self):
        """Test _sort_by_image also filters out invalid results."""
        from apps.ai.services.ranking import _sort_by_image
        results = [
            {'title': 'Valid', 'url': 'http://test.com/1'},
            {'url': 'http://test.com/2'},  # No title - invalid
        ]
        sorted_results = _sort_by_image(results)
        assert len(sorted_results) == 1
        assert sorted_results[0]['title'] == 'Valid'

    def test_apply_ranking(self):
        """Test _apply_ranking reorders results correctly."""
        from apps.ai.services.ranking import _apply_ranking
        results = [
            {'title': 'A', 'url': 'http://test.com/0'},
            {'title': 'B', 'url': 'http://test.com/1'},
            {'title': 'C', 'url': 'http://test.com/2'},
        ]
        ranked = _apply_ranking(results, [2, 0, 1])
        assert ranked[0]['title'] == 'C'
        assert ranked[1]['title'] == 'A'
        assert ranked[2]['title'] == 'B'

    def test_apply_ranking_handles_invalid_indices(self):
        """Test _apply_ranking ignores out-of-bounds indices."""
        from apps.ai.services.ranking import _apply_ranking
        results = [
            {'title': 'A', 'url': 'http://test.com/0'},
            {'title': 'B', 'url': 'http://test.com/1'},
        ]
        ranked = _apply_ranking(results, [1, 99, 0, -1])  # 99 and -1 are invalid
        assert len(ranked) == 2
        assert ranked[0]['title'] == 'B'
        assert ranked[1]['title'] == 'A'

    def test_apply_ranking_handles_duplicates(self):
        """Test _apply_ranking ignores duplicate indices."""
        from apps.ai.services.ranking import _apply_ranking
        results = [
            {'title': 'A', 'url': 'http://test.com/0'},
            {'title': 'B', 'url': 'http://test.com/1'},
        ]
        ranked = _apply_ranking(results, [1, 1, 0, 0])
        assert len(ranked) == 2
        assert ranked[0]['title'] == 'B'
        assert ranked[1]['title'] == 'A'

    def test_apply_ranking_adds_missing(self):
        """Test _apply_ranking appends results not in ranking."""
        from apps.ai.services.ranking import _apply_ranking
        results = [
            {'title': 'A', 'url': 'http://test.com/0'},
            {'title': 'B', 'url': 'http://test.com/1'},
            {'title': 'C', 'url': 'http://test.com/2'},
        ]
        # Only rank first two, third should be appended
        ranked = _apply_ranking(results, [1, 0])
        assert len(ranked) == 3
        assert ranked[0]['title'] == 'B'
        assert ranked[1]['title'] == 'A'
        assert ranked[2]['title'] == 'C'

    def test_rank_results_empty_list(self):
        """Test rank_results handles empty list."""
        from apps.ai.services.ranking import rank_results
        result = rank_results('pizza', [])
        assert result == []

    def test_rank_results_single_item(self):
        """Test rank_results returns single item unchanged."""
        from apps.ai.services.ranking import rank_results
        results = [{'title': 'Pizza', 'url': 'http://test.com/1'}]
        result = rank_results('pizza', results)
        assert len(result) == 1
        assert result[0]['title'] == 'Pizza'

    def test_rank_results_falls_back_without_key(self):
        """Test rank_results falls back to image sort without API key."""
        from apps.ai.services.ranking import rank_results
        settings = AppSettings.get()
        settings.openrouter_api_key = ''
        settings.save()

        results = [
            {'title': 'No Image', 'url': 'http://test.com/1'},
            {'title': 'Has Image', 'url': 'http://test.com/2', 'image_url': 'http://img.com/2.jpg'},
        ]
        result = rank_results('pizza', results)
        assert result[0]['title'] == 'Has Image'


class FixturesIntegrationTests(TestCase):
    """Tests that use the fixtures module to verify validation."""

    def setUp(self):
        self.validator = AIResponseValidator()

    def test_all_valid_fixtures_pass_validation(self):
        """Test all valid fixtures pass their respective validations."""
        test_cases = [
            ('recipe_remix', fixtures.VALID_RECIPE_REMIX),
            ('recipe_remix', fixtures.VALID_RECIPE_REMIX_MINIMAL),
            ('serving_adjustment', fixtures.VALID_SERVING_ADJUSTMENT),
            ('serving_adjustment', fixtures.VALID_SERVING_ADJUSTMENT_MINIMAL),
            ('serving_adjustment', fixtures.VALID_SERVING_ADJUSTMENT_WITH_NULLS),
            ('tips_generation', fixtures.VALID_TIPS_GENERATION),
            ('tips_generation', fixtures.VALID_TIPS_GENERATION_MAX),
            ('timer_naming', fixtures.VALID_TIMER_NAMING),
            ('remix_suggestions', fixtures.VALID_REMIX_SUGGESTIONS),
            ('discover_seasonal', fixtures.VALID_DISCOVER_SUGGESTIONS),
            ('discover_favorites', fixtures.VALID_DISCOVER_SUGGESTIONS),
            ('discover_new', fixtures.VALID_DISCOVER_SUGGESTIONS),
            ('search_ranking', fixtures.VALID_SEARCH_RANKING),
            ('selector_repair', fixtures.VALID_SELECTOR_REPAIR),
            ('selector_repair', fixtures.VALID_SELECTOR_REPAIR_LOW_CONFIDENCE),
            ('nutrition_estimate', fixtures.VALID_NUTRITION_ESTIMATE),
            ('nutrition_estimate', fixtures.VALID_NUTRITION_ESTIMATE_MINIMAL),
        ]
        for prompt_type, fixture in test_cases:
            result = self.validator.validate(prompt_type, fixture)
            assert result is not None, f'Validation failed for {prompt_type}'

    def test_all_invalid_fixtures_fail_validation(self):
        """Test all invalid fixtures fail their respective validations."""
        test_cases = [
            ('recipe_remix', fixtures.INVALID_RECIPE_REMIX_MISSING_TITLE),
            ('recipe_remix', fixtures.INVALID_RECIPE_REMIX_MISSING_INGREDIENTS),
            ('recipe_remix', fixtures.INVALID_RECIPE_REMIX_WRONG_TYPE_INGREDIENTS),
            ('recipe_remix', fixtures.INVALID_RECIPE_REMIX_WRONG_TYPE_TITLE),
            ('tips_generation', fixtures.INVALID_TIPS_TOO_FEW),
            ('tips_generation', fixtures.INVALID_TIPS_TOO_MANY),
            ('tips_generation', fixtures.INVALID_TIPS_WRONG_TYPE),
            ('tips_generation', fixtures.INVALID_TIPS_WRONG_ITEM_TYPE),
            ('remix_suggestions', fixtures.INVALID_REMIX_SUGGESTIONS_WRONG_COUNT),
            ('timer_naming', fixtures.INVALID_TIMER_NAMING_MISSING_LABEL),
            ('search_ranking', fixtures.INVALID_SEARCH_RANKING_WRONG_TYPE),
            ('selector_repair', fixtures.INVALID_SELECTOR_REPAIR_MISSING_CONFIDENCE),
            ('selector_repair', fixtures.INVALID_SELECTOR_REPAIR_WRONG_CONFIDENCE_TYPE),
            ('discover_seasonal', fixtures.INVALID_DISCOVER_MISSING_QUERY),
            ('discover_seasonal', fixtures.INVALID_DISCOVER_WRONG_ITEM_TYPE),
            ('nutrition_estimate', fixtures.INVALID_NUTRITION_MISSING_CALORIES),
            ('serving_adjustment', fixtures.INVALID_SERVING_ADJUSTMENT_MISSING_INGREDIENTS),
            ('serving_adjustment', fixtures.INVALID_SERVING_ADJUSTMENT_WRONG_TIME_TYPE),
        ]
        for prompt_type, fixture in test_cases:
            with pytest.raises(ValidationError):
                self.validator.validate(prompt_type, fixture)

    def test_get_fixture_helper(self):
        """Test the get_fixture helper function."""
        result = fixtures.get_fixture('valid_recipe_remix')
        assert result == fixtures.VALID_RECIPE_REMIX

    def test_get_fixture_not_found(self):
        """Test get_fixture raises KeyError for unknown fixture."""
        with pytest.raises(KeyError):
            fixtures.get_fixture('nonexistent_fixture')
