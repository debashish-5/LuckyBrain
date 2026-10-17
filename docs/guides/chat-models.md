# Chat models

LuckyBrain currently ships synchronous wrappers for OpenAI chat completions
and Groq chat completions. They send messages directly to the selected
provider; they do not retrieve documents, persist conversations, or orchestrate
tools.

## Choose a provider

```python
from luckybrain.core.models import GroqBrain, OpenaiBrain

openai_model = OpenaiBrain(model="gpt-4o-mini")
groq_model = GroqBrain(model="llama-3.3-70b-versatile")
```

Set `OPENAI_API_KEY` or `GROQ_API_KEY` in the environment, or pass `api_key`
when constructing the matching client. Avoid hard-coding credentials or
including them in logs and source control. Provider key availability and model
IDs are controlled by the provider account and can change independently of
LuckyBrain.

## Constructor options

Both clients accept these common options:

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `model` | `str` | Provider-specific | Model identifier sent unchanged to the provider. |
| `temperature` | `float \| None` | `None` | Sampling temperature; `None` leaves the provider default. Values must be between 0 and 2. |
| `api_key` | `str \| None` | `None` | Optional provider credential. Groq also falls back to `GROQ_API_KEY`; OpenAI uses its SDK's standard environment behavior. |
| `system_prompt` | `str` | `"You are a helpful assistant."` | Initial system instruction; cannot be blank. |
| `max_tokens` | `int \| None` | `None` | Optional positive response-token limit. |
| `top_p` | `float \| None` | `None` | Optional nucleus sampling value greater than 0 and at most 1. |
| `**additional_params` | provider-specific | — | Other options forwarded to the SDK, for example `seed` when supported by that endpoint. Reserved request fields cannot be overridden. |

`OpenaiBrain` also accepts `base_url: str | None = None` to target a compatible
chat-completions endpoint. This changes the destination, not the supported
capabilities: model compatibility and options depend on that endpoint.
`GroqBrain` uses the Groq SDK endpoint.

## Send text or messages

`think()` accepts a non-empty string or a non-empty sequence of text messages.
Each message uses one of the `user`, `assistant`, `system`, or `developer`
roles:

```python
answer = openai_model.think("Summarize this paragraph.")

answer = openai_model.think(
    [
        {"role": "user", "content": "Explain this as a short checklist."},
    ]
)
```

An empty prompt, empty message body, unsupported role, or non-text role/content
raises `ValueError` before a provider request. Provider SDK errors are allowed
to propagate; handle rate limits, timeouts, and service failures at the
application boundary.

`think()` returns assistant text and records the completed exchange in the
in-memory `history`. Call `clear_history()` to retain the original system
instruction and discard the rest. History is process-local, unbounded, and not
thread-safe; create/manage client instances accordingly.

## Stream output

```python
for piece in groq_model.stream("Give me three short project names."):
    print(piece, end="", flush=True)
print()
```

`stream()` returns an iterator of text chunks. The prompt and joined response
are added to history only after the iterator is consumed to completion. If a
consumer stops early or an SDK error interrupts iteration, that partial turn
is not recorded as a complete exchange. Streaming does not return usage
metadata.

## Implement another provider

Subclass `BaseChatModel` and implement `_complete(messages)` and
`_stream(messages)` using the provider SDK. The base class owns validation,
input normalization, and conversation behavior. Keep SDK-specific response
types inside the adapter; surface provider failures rather than returning
success-shaped placeholders. See the [API reference](../api-reference.md#chat-models).

## Scope and operational notes

- Calls are synchronous and can block the calling thread.
- The clients do not configure an application-level timeout, retry policy,
  concurrency limit, or durable storage.
- Provider model availability, rate limits, content policies, and accepted
  parameters are provider-controlled.
- Do not treat generated text as trusted instructions or as verified facts.
- These alpha clients are examples of adapters, not a production SLA.

For security, privacy, and deployment considerations, see
[Production readiness](production-readiness.md).
