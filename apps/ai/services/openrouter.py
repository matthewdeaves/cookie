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
        if api_key is None:
            settings = AppSettings.get()
            api_key = settings.openrouter_api_key

        if not api_key:
            raise AIUnavailableError("OpenRouter API key not configured")

        self.api_key = api_key

    def _parse_json_response(self, content: str) -> dict:
        """Parse JSON from AI response, handling markdown code blocks."""
        try:
            if content.startswith("```"):
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
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Send a completion request to OpenRouter."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        timeout_ms = timeout * 1000

        try:
            with OpenRouter(api_key=self.api_key) as client:
                response = client.chat.send(
                    messages=messages,
                    model=model,
                    stream=False,
                    timeout_ms=timeout_ms,
                )

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
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Async version of complete()."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        timeout_ms = timeout * 1000

        try:
            async with OpenRouter(api_key=self.api_key) as client:
                response = await client.chat.send_async(
                    messages=messages,
                    model=model,
                    stream=False,
                    timeout_ms=timeout_ms,
                )

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
        """Get list of available models from OpenRouter."""
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
        """Test if an API key is valid by making a minimal request."""
        try:
            service = cls(api_key=api_key)
            service.complete(
                system_prompt='Respond with exactly: {"status": "ok"}',
                user_prompt="Test connection",
                model="anthropic/claude-3.5-haiku",
                json_response=True,
                timeout=10,
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
        """Validate API key with caching to avoid excessive API calls."""
        if api_key is None:
            settings = AppSettings.get()
            api_key = settings.openrouter_api_key

        if not api_key:
            return False, "No API key configured"

        key_hash = hash(api_key)
        now = time.time()

        if key_hash in cls._key_validation_cache:
            is_valid, timestamp = cls._key_validation_cache[key_hash]
            if now - timestamp < cls.KEY_VALIDATION_TTL:
                return is_valid, None if is_valid else "API key is invalid or expired"

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
