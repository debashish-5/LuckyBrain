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
- [Query rewriting](guides/query-rewriting.md) — experimental query helper.
- [RAG and agent contracts](guides/contracts.md) — implementing the async
  protocols yourself.
- [API reference](api-reference.md) — signatures and documentation generated
  directly from source.
