# Get started

LuckyBrain is an early-stage Python package. This page gets you to the APIs
that exist today without implying that the unfinished pipelines already exist.

## Requirements

- Python 3.11 or newer.
- An API key only if you make a live request to OpenAI or Groq.

## Install

Install the package from the project root:

```bash
python -m pip install .
```

To work on the project, install its development tools instead:

```powershell
python -m pip install -e ".[dev]"
```

## Make a chat request

Set the key for your chosen provider in your shell or secret manager:

```powershell
$env:OPENAI_API_KEY = "your-key"
```

Then create a client and send a prompt:

```python
from luckybrain.core.models import OpenaiBrain

brain = OpenaiBrain(
    model="gpt-4o-mini",
    temperature=0.2,
    system_prompt="Answer in plain language.",
)
answer = brain.think("What does a retriever do?")
print(answer)
```

The call contacts the provider and is synchronous. `think()` remembers the
user and assistant messages in this client instance. The
[chat models guide](guides/chat-models.md) covers streaming, options,
history, error behavior, and Groq.

## Use prompt templates

`PromptFormat` helps you keep prompt text reusable and validate required
variables before sending a request:

```python
from luckybrain.prompts import PromptFormat

prompt = PromptFormat(
    "Summarize {topic} for a {audience} audience in {length} bullet points."
)

formatted = prompt.format(
    topic="retrieval-augmented generation",
    audience="technical",
    length="three",
)
print(formatted)

partial = prompt.partial(topic="retrieval-augmented generation")
print(partial.format(audience="non-technical", length="five"))
```

This is useful when you want the same prompt skeleton across several requests
without duplicating the template string or losing validation.

## Use a domain model

`Document` and `RetrievalResult` are lightweight data types; they do not read
files, retrieve records, or rank results:

```python
from luckybrain import Document, RetrievalResult

source = Document(
    id="handbook-12",
    content="Requests are handled within two business days.",
    metadata={"source": "handbook.pdf", "page": 12},
)
candidate = RetrievalResult(document=source, score=0.91)
```

## Where to go next

- [Chat models](guides/chat-models.md) — provider setup and model parameters.
- [Prompt templating](guides/prompt-formatting.md) — reusable prompts with validation.
- [Query rewriting](guides/query-rewriting.md) — experimental query helper.
- [RAG and agent contracts](guides/contracts.md) — implementing the async
  protocols yourself.
- [Text embeddings](guides/embeddings.md) — install and connect the optional
  local embedding model and in-memory vector index.
- [API reference](api-reference.md) — signatures and documentation generated
  directly from source.
