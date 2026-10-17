# Provider Chat Clients

LuckyBrain currently includes small synchronous chat clients for OpenAI and
Groq. They wrap each provider's Python SDK; they are not interchangeable with
the asynchronous protocols in `luckybrain.rag`, and they do not implement a
retrieval pipeline.

## Installation and API keys

Install LuckyBrain and its declared dependencies:

```bash
python -m pip install .
```

Set the environment variable for the provider you use:

```powershell
$env:OPENAI_API_KEY = "your-openai-api-key"
$env:GROQ_API_KEY = "your-groq-api-key"
```

In production, use your platform's secret manager rather than putting API keys
in source code. You only need to set the key for the client you use. Both SDKs
also support their standard environment-based key configuration.

Import the classes from `luckybrain.core.models`:

```python
from luckybrain.core.models import GroqBrain, OpenaiBrain
```

These client classes are not currently re-exported from `luckybrain` or
`luckybrain.core`.

## OpenAI

```python
from luckybrain.core.models import OpenaiBrain

brain = OpenaiBrain(
    model="gpt-4o-mini",
    temperature=0.2,
    system_prompt="Answer clearly and concisely.",
)
answer = brain.think("What is retrieval-augmented generation?")
print(answer)
```

`OpenaiBrain` accepts these constructor arguments:

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | `str` | `"gpt-4o-mini"` | OpenAI chat model name. |
| `temperature` | `float \| None` | `None` | Sampling temperature. `None` leaves the provider default in effect. |
| `api_key` | `str \| None` | `None` | Optional API key passed to the OpenAI SDK. When omitted, the SDK uses its standard `OPENAI_API_KEY` configuration. |
| `system_prompt` | `str` | `"You are a helpful assistant."` | Initial system message for the conversation. |
| `max_tokens` | `int \| None` | `None` | Optional response token limit passed to the provider. |
| `top_p` | `float \| None` | `None` | Optional nucleus-sampling value from greater than 0 through 1. |
| `base_url` | `str \| None` | `None` | Optional endpoint override for OpenAI-compatible services. |
| `**additional_params` | provider-specific | — | Extra chat-completion options forwarded to the SDK, such as `seed` or `presence_penalty`. |

## Groq

```python
from luckybrain.core.models import GroqBrain

brain = GroqBrain(
    model="llama-3.3-70b-versatile",
    temperature=0.2,
    system_prompt="Answer clearly and concisely.",
)
answer = brain.think("What is retrieval-augmented generation?")
print(answer)
```

`GroqBrain` accepts the same model, generation, and extra completion options,
with these provider-specific details (it does not accept OpenAI-specific
`base_url`):

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | `str` | `"llama-3.3-70b-versatile"` | Groq chat model name. |
| `temperature` | `float \| None` | `None` | Sampling temperature. `None` leaves the provider default in effect. |
| `api_key` | `str \| None` | `None` | Optional API key. If omitted or empty, the client reads `GROQ_API_KEY` from the environment. |
| `system_prompt` | `str` | `"You are a helpful assistant."` | Initial system message for the conversation. |

## Calling and streaming

Both clients provide the following methods:

| Method | Returns | Behavior |
| --- | --- | --- |
| `think(prompt: str)` | `str` | Sends a prompt and returns the assistant's complete text response. |
| `stream(prompt: str)` | `Iterator[str]` | Yields response text as chunks arrive from the provider. |

For example, stream a response with Groq:

```python
brain = GroqBrain()
for text_chunk in brain.stream("Give me three short project names."):
    print(text_chunk, end="", flush=True)
print()
```

Each client keeps an in-memory `history` initialized with its system prompt.
`think()` adds the prompt and returned assistant text to this history, so
later calls continue the conversation. It accepts either a string prompt or a
sequence of text messages with `user`, `assistant`, `system`, or `developer`
roles.
`stream()` adds the prompt and the accumulated response to history once the
stream is consumed fully; an interrupted stream is not recorded as a completed
turn. Call `clear_history()` to discard conversation turns while retaining the
initial system prompt.

The clients make synchronous network requests. Provider SDK/API errors are
propagated to the caller; configure retries or error handling in the
application as needed. If a non-text response is returned from `think()`,
the client raises `RuntimeError`.

## Extending the model base

`BaseChatModel` in `luckybrain.core.models` centralizes configuration
validation, text-message handling, conversation history, and the `think()` and
`stream()` methods. A custom synchronous provider adapter can
subclass it and implement `_complete(messages)` and `_stream(messages)` for its
SDK. Model identifiers are passed through to the provider rather than checked
against a hard-coded catalog. `OpenaiBrain` can also target an OpenAI-compatible
endpoint with `base_url`.

## Current scope

- The clients do not perform retrieval, prompt templating, or persistence.
- Conversation history is held only in process memory and is not thread-safe.
- Streaming does not yield usage metadata. Stream history updates only after
  complete consumption of the iterator.
- The clients require their respective provider SDKs, which are declared as
  LuckyBrain runtime dependencies.
