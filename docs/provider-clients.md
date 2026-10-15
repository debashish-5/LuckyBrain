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
answer = brain.invoke("What is retrieval-augmented generation?")
print(answer)
```

`OpenaiBrain` accepts these constructor arguments:

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `model` | `str` | `"gpt-4o-mini"` | OpenAI chat model name. |
| `temperature` | `float \| None` | `None` | Sampling temperature. `None` leaves the provider default in effect. |
| `api_key` | `str \| None` | `None` | Optional API key passed to the OpenAI SDK. When omitted, the SDK uses its standard `OPENAI_API_KEY` configuration. |
| `system_prompt` | `str` | `"You are a helpful assistant."` | Initial system message for the conversation. |

## Groq

```python
from luckybrain.core.models import GroqBrain

brain = GroqBrain(
    model="llama-3.3-70b-versatile",
    temperature=0.2,
    system_prompt="Answer clearly and concisely.",
)
answer = brain.invoke("What is retrieval-augmented generation?")
print(answer)
```

`GroqBrain` accepts the same arguments, with these provider-specific details:

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
| `invoke(prompt: str)` | `str` | Sends a prompt and returns the assistant's complete text response. |
| `stream(prompt: str)` | `Iterator[str]` | Yields response text as chunks arrive from the provider. |

For example, stream a response with Groq:

```python
brain = GroqBrain()
for text_chunk in brain.stream("Give me three short project names."):
    print(text_chunk, end="", flush=True)
print()
```

Each client keeps an in-memory `history` initialized with its system prompt.
`invoke()` adds the user prompt and returned assistant text to this history, so
later calls to `invoke()` continue the conversation. `stream()` includes the
current history and the supplied prompt in its request but does not add either
the streamed prompt or response to history. It is therefore a one-off request
unless you separately manage the conversation.

The clients make synchronous network requests. Provider SDK/API errors are
propagated to the caller; configure retries or error handling in the
application as needed. If a non-text response is returned from `invoke()`,
the client raises `RuntimeError`.

## Current scope

- The clients do not perform retrieval, prompt templating, or persistence.
- Conversation history is held only in process memory and is not thread-safe.
- Streaming does not yield usage metadata or update conversation history.
- The clients require their respective provider SDKs, which are declared as
  LuckyBrain runtime dependencies.
