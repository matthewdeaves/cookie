"""OpenRouter API service using the official SDK."""

import json
import logging
import time
from typing import Any

from openrouter import OpenRouter

from apps.core.models import AppSettings

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Base exception for AI service errors."""

    pass


class AIUnavailableError(AIServiceError):
    """Raised when AI service is not available (no API key)."""

    pass


class AIResponseError(AIServiceError):
    """Raised when AI returns an invalid or unexpected response."""

    pass


class OpenRouterService:
    """Service for interacting with OpenRouter API."""

    # Class-level cache for API key validation: {key_hash: (is_valid, timestamp)}
    _key_validation_cache: dict[int, tuple[bool, float]] = {}
    KEY_VALIDATION_TTL = 300  # 5 minutes

    def __init__(self, api_key: str | None = None):
        """Initialize the service with an API key.

        Args:
            api_key: OpenRouter API key. If None, fetches from AppSettings.
        """
        if api_key is None:
            settings = AppSettings.get()
            api_key = settings.openrouter_api_key

        if not api_key:
            raise AIUnavailableError("OpenRouter API key not configured")

        self.api_key = api_key

    def _parse_json_response(self, content: str) -> dict:
        """Parse JSON from AI response, handling markdown code blocks.

        Args:
            content: Raw response content from the AI.

        Returns:
            Parsed JSON as a dict.

        Raises:
            AIResponseError: If the content is not valid JSON.
        """
        try:
            # Handle potential markdown code blocks
            if content.startswith("```"):
                # Extract JSON from code block
                lines = content.split("\n")
                json_lines = []
                in_block = False
                for line in lines:
                    if line.startswith("```"):
                        in_block = not in_block
                        continue
                    if in_block:
                        json_lines.append(line)
                content = "\n".join(json_lines)

            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {content}")
            raise AIResponseError(f"Invalid JSON in AI response: {e}")

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "anthropic/claude-3.5-haiku",
        json_response: bool = True,
    ) -> dict[str, Any]:
        """Send a completion request to OpenRouter.

        Args:
            system_prompt: System message for the AI.
            user_prompt: User message/query.
            model: Model identifier (e.g., 'anthropic/claude-3.5-haiku').
            json_response: Whether to request JSON output.

        Returns:
            Parsed JSON response from the AI, or raw text response.

        Raises:
            AIUnavailableError: If no API key is configured.
            AIResponseError: If the response is invalid.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            with OpenRouter(api_key=self.api_key) as client:
                response = client.chat.send(
                    messages=messages,
                    model=model,
                    stream=False,
                )

            # Extract the response content
            if not response or not hasattr(response, "choices"):
                raise AIResponseError("Invalid response structure from OpenRouter")

            if not response.choices:
                raise AIResponseError("No choices in OpenRouter response")

            content = response.choices[0].message.content

            if json_response:
                return self._parse_json_response(content)

            return {"content": content}

        except AIServiceError:
            raise
        except Exception as e:
            logger.exception("OpenRouter API error")
            raise AIResponseError(f"OpenRouter API error: {e}")

    async def complete_async(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "anthropic/claude-3.5-haiku",
        json_response: bool = True,
    ) -> dict[str, Any]:
        """Async version of complete().

        Args:
            system_prompt: System message for the AI.
            user_prompt: User message/query.
            model: Model identifier (e.g., 'anthropic/claude-3.5-haiku').
            json_response: Whether to request JSON output.

        Returns:
            Parsed JSON response from the AI, or raw text response.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            async with OpenRouter(api_key=self.api_key) as client:
                response = await client.chat.send_async(
                    messages=messages,
                    model=model,
                    stream=False,
                )

            # Extract the response content
            if not response or not hasattr(response, "choices"):
                raise AIResponseError("Invalid response structure from OpenRouter")

            if not response.choices:
                raise AIResponseError("No choices in OpenRouter response")

            content = response.choices[0].message.content

            if json_response:
                return self._parse_json_response(content)

            return {"content": content}

        except AIServiceError:
            raise
        except Exception as e:
            logger.exception("OpenRouter API error")
            raise AIResponseError(f"OpenRouter API error: {e}")

    @classmethod
    def is_available(cls) -> bool:
        """Check if AI service is available (API key configured)."""
        settings = AppSettings.get()
        return bool(settings.openrouter_api_key)

    def get_available_models(self) -> list[dict[str, str]]:
        """Get list of available models from OpenRouter.

        Returns:
            List of dicts with 'id' and 'name' keys for each available model.

        Raises:
            AIResponseError: If the API call fails.
        """
        try:
            with OpenRouter(api_key=self.api_key) as client:
                response = client.models.list()

            if not response or not hasattr(response, "data"):
                raise AIResponseError("Invalid response from OpenRouter models API")

            models = [
                {"id": model.id, "name": model.name}
                for model in response.data
                if hasattr(model, "id") and hasattr(model, "name")
            ]
            return sorted(models, key=lambda m: m["name"].lower())
        except AIServiceError:
            raise
        except Exception as e:
            logger.exception("Failed to fetch OpenRouter models")
            raise AIResponseError(f"Failed to fetch available models: {e}")

    @classmethod
    def test_connection(cls, api_key: str) -> tuple[bool, str]:
        """Test if an API key is valid by making a minimal request.

        Args:
            api_key: The API key to test.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            service = cls(api_key=api_key)
            # Make a minimal test request
            service.complete(
                system_prompt='Respond with exactly: {"status": "ok"}',
                user_prompt="Test connection",
                model="anthropic/claude-3.5-haiku",
                json_response=True,
            )
            return True, "Connection successful"
        except AIUnavailableError:
            return False, "API key not provided"
        except AIResponseError as e:
            return False, f"API error: {e}"
        except Exception as e:
            return False, f"Connection failed: {e}"

    @classmethod
    def validate_key_cached(cls, api_key: str | None = None) -> tuple[bool, str | None]:
        """Validate API key with caching to avoid excessive API calls.

        Args:
            api_key: API key to validate. If None, fetches from AppSettings.

        Returns:
            Tuple of (is_valid: bool, error_message: str | None)
        """
        if api_key is None:
            settings = AppSettings.get()
            api_key = settings.openrouter_api_key

        if not api_key:
            return False, "No API key configured"

        key_hash = hash(api_key)
        now = time.time()

        # Check cache
        if key_hash in cls._key_validation_cache:
            is_valid, timestamp = cls._key_validation_cache[key_hash]
            if now - timestamp < cls.KEY_VALIDATION_TTL:
                return is_valid, None if is_valid else "API key is invalid or expired"

        # Validate with API
        try:
            is_valid, message = cls.test_connection(api_key)
            cls._key_validation_cache[key_hash] = (is_valid, now)
            return is_valid, None if is_valid else message
        except Exception as e:
            logger.exception("Failed to validate API key")
            return False, f"Unable to verify API key: {e}"

    @classmethod
    def invalidate_key_cache(cls):
        """Clear validation cache (call when key is updated)."""
        cls._key_validation_cache.clear()
