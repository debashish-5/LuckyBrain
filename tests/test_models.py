from types import SimpleNamespace
from typing import Any

import pytest

from luckybrain import Document, RetrievalResult
from luckybrain.core import models
from luckybrain.core.models import BaseChatModel, GroqBrain, OpenaiBrain


def test_document_keeps_metadata_and_has_independent_defaults() -> None:
    first = Document(id="doc-1", content="Text", metadata={"source": "guide"})
    second = Document(id="doc-2", content="Other text")

    assert first.metadata == {"source": "guide"}
    assert second.metadata == {}
    assert first.metadata is not second.metadata


@pytest.mark.parametrize(
    ("document_id", "content"),
    [("", "Text"), ("   ", "Text"), ("doc-1", ""), ("doc-1", "  ")],
)
def test_document_rejects_empty_identity_or_content(document_id: str, content: str) -> None:
    with pytest.raises(ValueError):
        Document(id=document_id, content=content)


def test_retrieval_result_keeps_document_and_score() -> None:
    document = Document(id="doc-1", content="Text")

    result = RetrievalResult(document=document, score=0.92)

    assert result.document is document
    assert result.score == 0.92


class FakeCompletions:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.empty_response = False

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        if kwargs.get("stream"):
            return [
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="Hi"))]),
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="!"))]),
            ]
        if self.empty_response:
            return SimpleNamespace(choices=[])
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Hello"))])


@pytest.fixture
def fake_clients(monkeypatch: pytest.MonkeyPatch) -> FakeCompletions:
    completions = FakeCompletions()
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    monkeypatch.setattr(models, "OpenAI", lambda **_: client)
    monkeypatch.setattr(models, "Groq", lambda **_: client)
    return completions


@pytest.mark.parametrize(
    "brain_class",
    [OpenaiBrain, GroqBrain],
)
def test_chat_clients_share_history_and_advanced_request_options(
    brain_class: type[OpenaiBrain] | type[GroqBrain],
    fake_clients: FakeCompletions,
) -> None:
    brain = brain_class(
        model="custom-model",
        system_prompt="Be concise.",
        max_tokens=128,
        top_p=0.8,
        seed=4,
    )

    assert not hasattr(brain, "invoke")
    assert brain.think("Hello") == "Hello"
    assert brain.think([{"role": "user", "content": "Again"}]) == "Hello"
    assert brain.history == [
        {"role": "system", "content": "Be concise."},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hello"},
        {"role": "user", "content": "Again"},
        {"role": "assistant", "content": "Hello"},
    ]
    assert fake_clients.calls[0]["model"] == "custom-model"
    assert fake_clients.calls[0]["max_tokens"] == 128
    assert fake_clients.calls[0]["top_p"] == 0.8
    assert fake_clients.calls[0]["seed"] == 4

    brain.clear_history()

    assert brain.history == [{"role": "system", "content": "Be concise."}]


@pytest.mark.parametrize("brain_class", [OpenaiBrain, GroqBrain])
def test_stream_updates_history_only_after_full_consumption(
    brain_class: type[OpenaiBrain] | type[GroqBrain],
    fake_clients: FakeCompletions,
) -> None:
    brain = brain_class()

    chunks = brain.stream("Hello")
    assert next(chunks) == "Hi"
    assert len(brain.history) == 1
    assert list(chunks) == ["!"]
    assert brain.history[-2:] == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"},
    ]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"model": " "}, "Model name"),
        ({"temperature": 2.1}, "Temperature"),
        ({"max_tokens": 0}, "max_tokens"),
        ({"top_p": 0}, "top_p"),
        ({"system_prompt": " "}, "System prompt"),
    ],
)
def test_chat_client_rejects_invalid_configuration(kwargs: dict[str, Any], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        OpenaiBrain(**kwargs)


def test_invalid_message_does_not_change_history() -> None:
    with pytest.raises(ValueError, match="Unsupported chat message role"):
        BaseChatModel._normalize_messages([{"role": "tool", "content": "invalid"}])


@pytest.mark.parametrize("brain_class", [OpenaiBrain, GroqBrain])
def test_empty_provider_response_raises_without_mutating_history(
    brain_class: type[OpenaiBrain] | type[GroqBrain],
    fake_clients: FakeCompletions,
) -> None:
    brain = brain_class()
    fake_clients.empty_response = True

    with pytest.raises(RuntimeError, match="did not contain any choices"):
        brain.think("Hello")

    assert brain.history == [{"role": "system", "content": "You are a helpful assistant."}]
