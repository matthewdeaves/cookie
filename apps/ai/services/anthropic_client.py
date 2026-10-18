"""Anthropic API service using the official SDK."""

import hashlib
import json
import logging
import time
from typing import Any

import anthropic

from apps.core.models import AppSettings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-haiku-5-5"
MAX_TOKENS = 4096


class AIServiceError(Exception):
    """Base exception for AI service errors."""

    pass


class AIUnavailableError(AIServiceError):
    """Raised when AI service is not available (no API key)."""

    pass


class AIResponseError(AIServiceError):
    """Raised when AI returns an invalid or unexpected response."""

    pass


class AnthropicService:
    """Service for interacting with the Anthropic API."""

    # Class-level cache for API key validation: {key_hash: (is_valid, timestamp)}
    _key_validation_cache: dict[int, tuple[bool, float]] = {}
    KEY_VALIDATION_TTL = 300  # 5 minutes

    def __init__(self, api_key: str | None = None):
        if api_key is None:
            settings = AppSettings.get()
            api_key = settings.anthropic_api_key

        if not api_key:
            raise AIUnavailableError("Anthropic API key not configured")

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

    @staticmethod
    def _extract_text(response: Any) -> str:
        """Concatenate the text blocks of a Messages API response."""
        blocks = getattr(response, "content", None)
        if not blocks:
            raise AIResponseError("No content in Anthropic response")

        text = "".join(b.text for b in blocks if getattr(b, "type", None) == "text" and isinstance(b.text, str))
        if not text:
            raise AIResponseError("No text content in Anthropic response")
        return text

    def _build_result(self, response: Any, json_response: bool) -> dict[str, Any]:
        content = self._extract_text(response)
        if json_response:
            return self._parse_json_response(content)
        return {"content": content}

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = DEFAULT_MODEL,
        json_response: bool = True,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Send a completion request to the Anthropic Messages API."""
        try:
            with anthropic.Anthropic(api_key=self.api_key, timeout=timeout, max_retries=1) as client:
                response = client.messages.create(
                    model=model,
                    max_tokens=MAX_TOKENS,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
            return self._build_result(response, json_response)

        except AIServiceError:
            raise
        except Exception as e:
            logger.exception("Anthropic API error")
            raise AIResponseError(f"Anthropic API error: {e}")

    async def complete_async(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = DEFAULT_MODEL,
        json_response: bool = True,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Async version of complete()."""
        try:
            async with anthropic.AsyncAnthropic(api_key=self.api_key, timeout=timeout, max_retries=1) as client:
                response = await client.messages.create(
                    model=model,
                    max_tokens=MAX_TOKENS,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
            return self._build_result(response, json_response)

        except AIServiceError:
            raise
        except Exception as e:
            logger.exception("Anthropic API error")
            raise AIResponseError(f"Anthropic API error: {e}")

    @classmethod
    def is_available(cls) -> bool:
        """Check if AI service is available (API key configured)."""
        settings = AppSettings.get()
        return bool(settings.anthropic_api_key)

    def get_available_models(self) -> list[dict[str, str]]:
        """Get list of available models from the Anthropic API."""
        try:
            with anthropic.Anthropic(api_key=self.api_key, timeout=30, max_retries=1) as client:
                page = client.models.list(limit=100)

            if not page or not hasattr(page, "data"):
                raise AIResponseError("Invalid response from Anthropic models API")

            models = [
                {"id": model.id, "name": getattr(model, "display_name", None) or model.id}
                for model in page.data
                if getattr(model, "id", None)
            ]
            return sorted(models, key=lambda m: m["name"].lower())
        except AIServiceError:
            raise
        except Exception as e:
            logger.exception("Failed to fetch Anthropic models")
            raise AIResponseError(f"Failed to fetch available models: {e}")

    @classmethod
    def test_connection(cls, api_key: str) -> tuple[bool, str]:
        """Test if an API key is valid by making a minimal request."""
        try:
            service = cls(api_key=api_key)
            service.complete(
                system_prompt='Respond with exactly: {"status": "ok"}',
                user_prompt="Test connection",
                model=DEFAULT_MODEL,
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
            api_key = settings.anthropic_api_key

        if not api_key:
            return False, "No API key configured"

        # SHA-256 used as a cache lookup key (not for password storage)
        cache_id = hashlib.sha256(api_key.encode()).hexdigest()  # nosec
        now = time.time()

        if cache_id in cls._key_validation_cache:
            is_valid, timestamp = cls._key_validation_cache[cache_id]
            if now - timestamp < cls.KEY_VALIDATION_TTL:
                return is_valid, None if is_valid else "API key is invalid or expired"

        try:
            is_valid, message = cls.test_connection(api_key)
            cls._key_validation_cache[cache_id] = (is_valid, now)
            return is_valid, None if is_valid else message
        except Exception as e:
            logger.exception("Failed to validate API key")
            return False, f"Unable to verify API key: {e}"

    @classmethod
    def invalidate_key_cache(cls):
        """Clear validation cache (call when key is updated)."""
        cls._key_validation_cache.clear()
