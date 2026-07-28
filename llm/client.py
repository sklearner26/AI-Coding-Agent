"""Thin wrapper around the Groq OpenAI-compatible API.

The environment variable is intentionally kept as OPENAI_API_KEY so the
rest of the project doesn't need to change. Only the provider changes.
"""

from __future__ import annotations

import json
import logging

from openai import APIError, APITimeoutError, AuthenticationError, OpenAI

from config import LLM_ENDPOINT, LLM_PROVIDER, LLMSettings

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    """Raised when the LLM cannot produce a usable response."""


class LLMClient:
    """Sends chat completions to Groq and returns raw or JSON-parsed text."""

    def __init__(self, settings: LLMSettings) -> None:
        # Validation raises RuntimeError with a clear message before any network call.
        settings.validate()

        self._settings = settings
        self._client = OpenAI(
            api_key=settings.api_key,
            base_url=LLM_ENDPOINT,
        )

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return raw text from a chat completion."""

        try:
            response = self._client.chat.completions.create(
                model=self._settings.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self._settings.temperature,
                max_tokens=self._settings.max_tokens,
            )

        except AuthenticationError as exc:
            raise LLMError(_format_api_error(exc)) from exc

        except APITimeoutError as exc:
            raise LLMError(f"Groq request timed out: {exc}") from exc

        except APIError as exc:
            raise LLMError(_format_api_error(exc)) from exc

        content = response.choices[0].message.content

        if not content:
            raise LLMError("Model returned an empty response")

        return content

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Return a JSON-parsed response."""

        raw = self.complete(system_prompt, user_prompt)
        cleaned = _strip_code_fences(raw)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LLMError(f"Invalid JSON returned by model: {exc}") from exc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_api_error(exc: APIError) -> str:
    """Build a status-code-aware error message with probable causes."""
    status = getattr(exc, "status_code", "unknown")
    body = getattr(exc, "body", None) or {}
    message = (
        body.get("error", {}).get("message", str(exc))
        if isinstance(body, dict)
        else str(exc)
    )

    if status == 401:
        causes = (
            "  - Invalid or expired API key\n"
            "  - Key does not start with 'gsk_'\n"
            "  - Get a valid key at https://console.groq.com/keys"
        )
        title = f"{LLM_PROVIDER} authentication failed."
    elif status == 429:
        causes = (
            "  - Rate limit exceeded — wait and retry\n"
            "  - Monthly quota exhausted — check https://console.x.ai/\n"
            "  - Too many concurrent requests"
        )
        title = f"{LLM_PROVIDER} rate limit hit."
    elif status == 404:
        causes = (
            f"  - Model name is wrong (check OPENAI_MODEL in .env)\n"
            f"  - Endpoint may have changed (current: {LLM_ENDPOINT})"
        )
        title = f"{LLM_PROVIDER} model not found."
    else:
        causes = (
            "  - Invalid API key\n"
            f"  - Wrong endpoint (expected: {LLM_ENDPOINT})\n"
            "  - API access not enabled\n"
            "  - Wrong or unsupported model name"
        )
        title = f"{LLM_PROVIDER} API error."

    return (
        f"{title}\n\n"
        f"HTTP {status}\n\n"
        f"Reason:\n{message}\n\n"
        f"Possible causes:\n{causes}"
    )


def _strip_code_fences(text: str) -> str:
    """Extract raw code strictly between markdown code fences if present."""
    lines = text.strip().splitlines()
    fence_indices = [i for i, line in enumerate(lines) if line.strip().startswith("```")]
    
    if len(fence_indices) >= 2:
        start_idx = fence_indices[0] + 1
        end_idx = fence_indices[-1]
        return "\n".join(lines[start_idx:end_idx]).strip()
    elif len(fence_indices) == 1:
        return "\n".join(lines[fence_indices[0] + 1:]).strip()
    
    return text.strip()
