"""Provider-neutral domain models and synchronous chat model clients."""

import os
from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from math import isfinite
from typing import Any, Protocol, TypedDict, cast

from groq import Groq
from groq.types.chat import ChatCompletionMessageParam as GroqChatCompletionMessageParam
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam as OpenAIChatCompletionMessageParam
import ollama
from messages.messages import to_dicts

def _messages(self, prompt):
    if isinstance(prompt, str):
        messages = [{"role": "user", "content": prompt}]
    else:
        messages = to_dicts(prompt)        # works with objects, dicts, or a mix

    if self.system_prompt and messages[0]["role"] != "system":
        messages.insert(0, {"role": "system", "content": self.system_prompt})
    return messages


class ChatMessage(TypedDict):
    """A text-based chat message accepted by the built-in clients."""

    role: str
    content: str


ChatInput = str | Sequence[Mapping[str, str]]


class BaseChatModel(ABC):
    """Shared conversation handling for synchronous chat model providers."""

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        temperature: float | None = None,
        system_prompt: str = "You are a helpful assistant.",
        max_tokens: int | None = None,
        top_p: float | None = None,
        **additional_params: Any,
    ) -> None:
        if not isinstance(model, str) or not model.strip():
            raise ValueError("Model name must not be empty.")
        if temperature is not None and (
            isinstance(temperature, bool)
            or not isinstance(temperature, (int, float))
            or not isfinite(temperature)
            or not 0 <= temperature <= 2
        ):
            raise ValueError("Temperature must be between 0 and 2.")
        if max_tokens is not None and (
            isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens < 1
        ):
            raise ValueError("max_tokens must be a positive integer.")
        if top_p is not None and (
            isinstance(top_p, bool)
            or not isinstance(top_p, (int, float))
            or not isfinite(top_p)
            or not 0 < top_p <= 1
        ):
            raise ValueError("top_p must be greater than 0 and at most 1.")
        if not isinstance(system_prompt, str) or not system_prompt.strip():
            raise ValueError("System prompt must not be empty.")
        reserved_params = {"model", "messages", "temperature", "stream"}
        collisions = reserved_params.intersection(additional_params)
        if collisions:
            raise ValueError(
                "Additional parameters cannot override " + ", ".join(sorted(collisions)) + "."
            )

        self.model = model
        self.temperature = temperature
        self.api_key = api_key
        self.additional_params = dict(additional_params)
        self.request_params: dict[str, Any] = dict(additional_params)
        if max_tokens is not None:
            self.request_params["max_tokens"] = max_tokens
        if top_p is not None:
            self.request_params["top_p"] = top_p
        self._system_message: ChatMessage = {
            "role": "system",
            "content": system_prompt,
        }
        self.history: list[ChatMessage] = [self._system_message.copy()]

    def think(self, messages: ChatInput) -> str:
        """Send a prompt or sequence of text messages and return the model's answer."""
        new_messages = self._normalize_messages(messages)
        request_messages = self.history + new_messages
        answer = self._complete(request_messages)
        self.history.extend(new_messages)
        self.history.append({"role": "assistant", "content": answer})
        return answer

    def stream(self, messages: ChatInput) -> Iterator[str]:
        """Stream a response and add the completed exchange to conversation history."""
        new_messages = self._normalize_messages(messages)
        request_messages = self.history + new_messages
        response_parts: list[str] = []
        for part in self._stream(request_messages):
            response_parts.append(part)
            yield part
        self.history.extend(new_messages)
        self.history.append({"role": "assistant", "content": "".join(response_parts)})

    def clear_history(self) -> None:
        """Clear conversation turns while preserving the initial system prompt."""
        self.history[:] = [self._system_message.copy()]

    @staticmethod
    def _normalize_messages(messages: ChatInput) -> list[ChatMessage]:
        if isinstance(messages, str):
            if not messages.strip():
                raise ValueError("Prompt must not be empty.")
            return [{"role": "user", "content": messages}]
        if not messages:
            raise ValueError("Messages must not be empty.")

        normalized: list[ChatMessage] = []
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            if not isinstance(role, str) or not isinstance(content, str):
                raise ValueError("Chat message role and content must be strings.")
            if role not in {"user", "assistant", "system", "developer"}:
                raise ValueError(f"Unsupported chat message role: {role!r}.")
            if not content.strip():
                raise ValueError("Chat message content must not be empty.")
            normalized.append({"role": role, "content": content})
        return normalized

    @abstractmethod
    def _complete(self, messages: list[ChatMessage]) -> str:
        """Make one non-streaming provider request."""

    @abstractmethod
    def _stream(self, messages: list[ChatMessage]) -> Iterator[str]:
        """Make one streaming provider request."""


class ChatModelProtocol(Protocol):
    """Common public interface implemented by synchronous chat models."""

    def think(self, messages: ChatInput) -> str: ...

    def stream(self, messages: ChatInput) -> Iterator[str]: ...

    def clear_history(self) -> None: ...


@dataclass(frozen=True, slots=True)
class Document:
    """A source document or passage with stable identity and metadata."""

    id: str
    content: str
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Document id must not be empty.")
        if not self.content.strip():
            raise ValueError("Document content must not be empty.")


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """A document returned by retrieval with its provider-defined relevance score."""

    document: Document
    score: float


class OpenaiBrain(BaseChatModel):
    """Synchronous chat client for OpenAI-compatible chat completion models."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float | None = None,
        api_key: str | None = None,
        system_prompt: str = "You are a helpful assistant.",
        max_tokens: int | None = None,
        top_p: float | None = None,
        base_url: str | None = None,
        **additional_params: Any,
    ) -> None:
        super().__init__(
            model=model,
            api_key=api_key,
            temperature=temperature,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            top_p=top_p,
            **additional_params,
        )
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def _complete(self, messages: list[ChatMessage]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=cast(
                list[OpenAIChatCompletionMessageParam],
                messages,
            ),
            **self.request_params,
        )
        if not response.choices:
            raise RuntimeError("The OpenAI response did not contain any choices.")
        answer = response.choices[0].message.content
        if not isinstance(answer, str):
            raise RuntimeError("The OpenAI response did not contain text.")
        return answer

    def _stream(self, messages: list[ChatMessage]) -> Iterator[str]:
        response_stream = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=cast(
                list[OpenAIChatCompletionMessageParam],
                messages,
            ),
            stream=True,
            **self.request_params,
        )
        for chunk in response_stream:
            if chunk.choices and (content := chunk.choices[0].delta.content) is not None:
                yield content


class GroqBrain(BaseChatModel):
    """Synchronous chat client for Groq chat completion models."""

    def __init__(
        self,
        model: str = "llama-3.3-70b-versatile",
        temperature: float | None = None,
        api_key: str | None = None,
        system_prompt: str = "You are a helpful assistant.",
        max_tokens: int | None = None,
        top_p: float | None = None,
        **additional_params: Any,
    ) -> None:
        super().__init__(
            model=model,
            api_key=api_key,
            temperature=temperature,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            top_p=top_p,
            **additional_params,
        )
        self.client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))

    def _complete(self, messages: list[ChatMessage]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=cast(
                list[GroqChatCompletionMessageParam],
                messages,
            ),
            **self.request_params,
        )
        if not response.choices:
            raise RuntimeError("The Groq response did not contain any choices.")
        answer = response.choices[0].message.content
        if not isinstance(answer, str):
            raise RuntimeError("The Groq response did not contain text.")
        return answer

    def _stream(self, messages: list[ChatMessage]) -> Iterator[str]:
        response_stream = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=cast(
                list[GroqChatCompletionMessageParam],
                messages,
            ),
            stream=True,
            **self.request_params,
        )
        for chunk in response_stream:
            if chunk.choices and (content := chunk.choices[0].delta.content) is not None:
                yield content





class OllamaBrain(BaseChatModel): 
    """Synchronous chat client for local or cloud Ollama models."""
    # Passed to Ollama as top-level arguments; every other extra parameter goes into `options`.
    _TOP_LEVEL_PARAMS = frozenset({"format", "keep_alive", "think"})
    def __init__(
            self,
            model:str = "mistral", 
            api_key: str | None = None, 
            temperature: float | None = None, 
            system_prompt: str = "You are a helpful assistant", 
            max_tokens: int | None = None, 
            top_p: float | None = None, 
            host: str | None = None, 
            **additional_params: Any
    ) -> None: 
        super().__init__(
            model = model, 
            api_key=api_key, 
            temperature=temperature, 
            system_prompt=system_prompt, 
            max_tokens=max_tokens, 
            top_p=top_p, 
            host = host, 
            **additional_params
        )
        api_key = api_key or os.getenv("OLLAMA_API_KEY")
        client_kwargs:dict[str,Any] = {}
        if api_key: 
            client_kwargs["headers"] = {"Authorization": f"Bearer {api_key}"}
        self.client = ollama.Client(host=host, **client_kwargs)

     def _chat_kwargs(self,messages:list[ChatMessage]) -> dict[str,Any]: 
        params = dict(self.request_params)
        options = dict(params.pop("options",None) or {})
        if self.temperature is None:
            options['temperature'] = self.temperature
        if 'max_tokens' in params:
            options['num_predict'] = params.pop("max_tokens")
        top_level = {key:params.pop(key) for key in self._TOP_LEVEL_PARAMS & params.keys()}
        options.update(params)
        kwargs:dict[str,Any] = {
            "model":self.model,
            "messages":[
                {
                    "role":"system" if m['role'] == "devloper" else m['role'], "content":m['content']
                } for m in messages
            ], **top_level
        }
        if options:
            kwargs['option'] = options
        return kwargs

    def _error(self, error: ollama.ResponseError) -> RuntimeError:
        if error.status_code == 404:
            return RuntimeError(f"Ollama model {self.model!r} not found. Run: ollama pull {self.model}")
        return RuntimeError(f"Ollama error ({error.status_code}): {error.error}")

    def _complete(self, messages:list[ChatMessage]) -> str: 
        try: 
            response = self.client.chat(**self._chat_kwargs(messages))
        except ollama.ResponseError as error: 
            raise self._error(error) from error
        answer = response.message.content   
        if not isinstance(response,str): 
            raise RuntimeError("The Ollama response did not contain text.")
        return answer

    def _stream(self, messages:list[ChatMessage]) -> str: 
        try: 
            for chunk in self.client.chat(**self._chat_kwargs(messages=messages),stream=True):
                if content := chunk.message.content: 
                    yield content
        except Exception as error: 
            raise self._error(error=error) from error
        
