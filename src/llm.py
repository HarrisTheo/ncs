"""Replaceable structured-LLM interface and local Ollama implementation."""

from __future__ import annotations

import os
from typing import Any, Protocol, TypeVar
from urllib.parse import urlparse

import httpx
import ollama
from pydantic import BaseModel, ValidationError


ResponseT = TypeVar("ResponseT", bound=BaseModel)
DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_TIMEOUT_SECONDS = 180.0
DEFAULT_CONTEXT_TOKENS = 8_192


class LLMError(RuntimeError):
    """Base error for failures at the model-provider boundary."""


class LLMConfigurationError(LLMError):
    """Raised when local model configuration is invalid."""


class LLMUnavailableError(LLMError):
    """Raised when Ollama or the configured model cannot be reached."""


class LLMTimeoutError(LLMError):
    """Raised when local inference exceeds the configured timeout."""


class LLMMalformedResponseError(LLMError):
    """Raised when provider output is missing or fails schema validation."""


class StructuredLLM(Protocol):
    """Provider-neutral interface used by future triage and reviewer stages."""

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseT],
    ) -> ResponseT:
        """Generate and validate one structured response."""
        ...


class OllamaLLM:
    """Local Ollama adapter for validated, non-streaming JSON responses."""

    def __init__(
        self,
        *,
        model: str | None = None,
        host: str | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        context_tokens: int = DEFAULT_CONTEXT_TOKENS,
        client: Any | None = None,
    ) -> None:
        configured_model = os.getenv("OLLAMA_MODEL", "") if model is None else model
        configured_host = (
            os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST) if host is None else host
        )
        self.model = configured_model.strip()
        self.host = configured_host.strip()

        if not self.model:
            raise LLMConfigurationError(
                "No Ollama model configured. Set OLLAMA_MODEL or pass model=."
            )
        if not _is_loopback_host(self.host):
            raise LLMConfigurationError(
                "OLLAMA_HOST must use localhost or a loopback address for this "
                "local-only MVP."
            )
        if timeout_seconds <= 0:
            raise LLMConfigurationError("timeout_seconds must be greater than zero")
        if context_tokens < 1:
            raise LLMConfigurationError("context_tokens must be greater than zero")

        self.timeout_seconds = float(timeout_seconds)
        self.context_tokens = context_tokens
        self._client = client or ollama.Client(
            host=self.host,
            timeout=self.timeout_seconds,
        )

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseT],
    ) -> ResponseT:
        """Request one JSON response and validate it with ``response_model``."""

        if not system_prompt.strip():
            raise LLMConfigurationError("system_prompt must not be empty")
        if not user_prompt.strip():
            raise LLMConfigurationError("user_prompt must not be empty")

        try:
            response = self._client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                format=response_model.model_json_schema(),
                options={
                    "temperature": 0,
                    "num_ctx": self.context_tokens,
                },
                think=False,
                stream=False,
            )
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(
                f"Ollama did not respond within {self.timeout_seconds:g} seconds."
            ) from exc
        except (ConnectionError, httpx.ConnectError) as exc:
            raise LLMUnavailableError(
                f"Ollama is unavailable at {self.host}. Start the local Ollama "
                "service and try again."
            ) from exc
        except ollama.RequestError as exc:
            raise LLMConfigurationError(f"Ollama rejected the request: {exc}") from exc
        except ollama.ResponseError as exc:
            raise LLMUnavailableError(
                f"Ollama could not use model '{self.model}': {exc}"
            ) from exc

        content = _response_content(response)
        try:
            return response_model.model_validate_json(content)
        except ValidationError as exc:
            details = "; ".join(
                f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
                for error in exc.errors(include_url=False, include_input=False)
            )
            raise LLMMalformedResponseError(
                f"Ollama returned data that does not match "
                f"{response_model.__name__}: {details}"
            ) from exc


def _response_content(response: Any) -> str:
    try:
        content = response.message.content
    except (AttributeError, TypeError) as exc:
        raise LLMMalformedResponseError(
            "Ollama returned a response without an assistant message."
        ) from exc

    if not isinstance(content, str) or not content.strip():
        raise LLMMalformedResponseError(
            "Ollama returned an empty or non-text assistant response."
        )
    return content


def _is_loopback_host(host: str) -> bool:
    parsed = urlparse(host)
    return parsed.scheme in {"http", "https"} and parsed.hostname in {
        "127.0.0.1",
        "localhost",
        "::1",
    }
