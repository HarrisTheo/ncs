from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import ollama
import pytest
from pydantic import BaseModel

from src.llm import (
    DEFAULT_CONTEXT_TOKENS,
    LLMConfigurationError,
    LLMMalformedResponseError,
    LLMTimeoutError,
    LLMUnavailableError,
    OllamaLLM,
    StructuredLLM,
)


class ExampleResponse(BaseModel):
    answer: str


def response_with(content: object) -> SimpleNamespace:
    return SimpleNamespace(message=SimpleNamespace(content=content))


def configured_client(mock_client: Mock) -> OllamaLLM:
    return OllamaLLM(model="test-model:1b", client=mock_client)


def test_uses_explicit_model_and_structured_request() -> None:
    mock_client = Mock()
    mock_client.chat.return_value = response_with('{"answer":"grounded"}')
    llm = configured_client(mock_client)

    result = llm.generate_structured(
        system_prompt="Use only supplied data.",
        user_prompt="Incident and policies",
        response_model=ExampleResponse,
    )

    assert result == ExampleResponse(answer="grounded")
    mock_client.chat.assert_called_once_with(
        model="test-model:1b",
        messages=[
            {"role": "system", "content": "Use only supplied data."},
            {"role": "user", "content": "Incident and policies"},
        ],
        format=ExampleResponse.model_json_schema(),
        options={"temperature": 0, "num_ctx": DEFAULT_CONTEXT_TOKENS},
        think=False,
        stream=False,
    )


def test_model_can_be_configured_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_MODEL", "configured-model:4b")
    mock_client = Mock()

    llm = OllamaLLM(client=mock_client)

    assert llm.model == "configured-model:4b"


def test_explicit_model_overrides_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_MODEL", "environment-model:4b")

    llm = OllamaLLM(model="explicit-model:8b", client=Mock())

    assert llm.model == "explicit-model:8b"


def test_constructs_ollama_client_with_host_and_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = Mock()
    client_factory = Mock(return_value=transport)
    monkeypatch.setattr("src.llm.ollama.Client", client_factory)

    llm = OllamaLLM(
        model="test-model",
        host="http://localhost:11434",
        timeout_seconds=45,
    )

    client_factory.assert_called_once_with(
        host="http://localhost:11434",
        timeout=45.0,
    )
    assert llm._client is transport


def test_missing_model_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)

    with pytest.raises(LLMConfigurationError, match="No Ollama model configured"):
        OllamaLLM(client=Mock())


@pytest.mark.parametrize(
    "host",
    [
        "http://ollama.internal:11434",
        "https://example.com",
        "127.0.0.1:11434",
        "",
    ],
)
def test_non_loopback_or_malformed_host_is_rejected(host: str) -> None:
    with pytest.raises(LLMConfigurationError, match="loopback"):
        OllamaLLM(model="test-model", host=host, client=Mock())


@pytest.mark.parametrize(
    "host",
    [
        "http://127.0.0.1:11434",
        "http://localhost:11434",
        "http://[::1]:11434",
    ],
)
def test_loopback_hosts_are_accepted(host: str) -> None:
    llm = OllamaLLM(model="test-model", host=host, client=Mock())

    assert llm.host == host


@pytest.mark.parametrize(
    ("argument", "value", "message"),
    [
        ("timeout_seconds", 0, "timeout_seconds"),
        ("context_tokens", 0, "context_tokens"),
    ],
)
def test_invalid_numeric_configuration_is_rejected(
    argument: str, value: int, message: str
) -> None:
    kwargs = {argument: value}

    with pytest.raises(LLMConfigurationError, match=message):
        OllamaLLM(model="test-model", client=Mock(), **kwargs)


@pytest.mark.parametrize(
    ("system_prompt", "user_prompt", "message"),
    [
        ("", "incident", "system_prompt"),
        ("system", "   ", "user_prompt"),
    ],
)
def test_empty_prompts_are_rejected(
    system_prompt: str, user_prompt: str, message: str
) -> None:
    llm = configured_client(Mock())

    with pytest.raises(LLMConfigurationError, match=message):
        llm.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=ExampleResponse,
        )


def test_connection_failure_has_clear_error() -> None:
    mock_client = Mock()
    mock_client.chat.side_effect = ConnectionError("connection refused")
    llm = configured_client(mock_client)

    with pytest.raises(LLMUnavailableError, match="Start the local Ollama service"):
        llm.generate_structured(
            system_prompt="system",
            user_prompt="incident",
            response_model=ExampleResponse,
        )


def test_timeout_has_clear_error() -> None:
    mock_client = Mock()
    mock_client.chat.side_effect = httpx.ReadTimeout("timed out")
    llm = OllamaLLM(model="test-model", timeout_seconds=12, client=mock_client)

    with pytest.raises(LLMTimeoutError, match="within 12 seconds"):
        llm.generate_structured(
            system_prompt="system",
            user_prompt="incident",
            response_model=ExampleResponse,
        )


def test_missing_model_response_has_clear_error() -> None:
    mock_client = Mock()
    mock_client.chat.side_effect = ollama.ResponseError("model not found", 404)
    llm = configured_client(mock_client)

    with pytest.raises(LLMUnavailableError, match="test-model:1b.*model not found"):
        llm.generate_structured(
            system_prompt="system",
            user_prompt="incident",
            response_model=ExampleResponse,
        )


def test_rejected_request_has_clear_configuration_error() -> None:
    mock_client = Mock()
    mock_client.chat.side_effect = ollama.RequestError("invalid request")
    llm = configured_client(mock_client)

    with pytest.raises(LLMConfigurationError, match="rejected.*invalid request"):
        llm.generate_structured(
            system_prompt="system",
            user_prompt="incident",
            response_model=ExampleResponse,
        )


@pytest.mark.parametrize(
    "response",
    [
        SimpleNamespace(),
        response_with(None),
        response_with(""),
    ],
)
def test_missing_or_empty_content_is_rejected(response: SimpleNamespace) -> None:
    mock_client = Mock()
    mock_client.chat.return_value = response
    llm = configured_client(mock_client)

    with pytest.raises(LLMMalformedResponseError):
        llm.generate_structured(
            system_prompt="system",
            user_prompt="incident",
            response_model=ExampleResponse,
        )


@pytest.mark.parametrize(
    "content",
    [
        "not json",
        "{}",
        '{"answer": 42}',
    ],
)
def test_invalid_structured_content_is_rejected_without_echoing_it(
    content: str,
) -> None:
    mock_client = Mock()
    mock_client.chat.return_value = response_with(content)
    llm = configured_client(mock_client)

    with pytest.raises(LLMMalformedResponseError) as error:
        llm.generate_structured(
            system_prompt="system",
            user_prompt="incident",
            response_model=ExampleResponse,
        )

    assert content not in str(error.value)


def test_provider_implements_replaceable_interface() -> None:
    llm: StructuredLLM = OllamaLLM(model="test-model", client=Mock())

    assert callable(llm.generate_structured)
