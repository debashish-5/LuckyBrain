# LuckyBrain

**Open foundations for retrieval-augmented generation and agent systems.**

LuckyBrain is an open-source Python project for building reliable, inspectable, and composable RAG components, with agent capabilities as a closely related part of the system. The long-term goal is ambitious; the project today is intentionally at its beginning.

> **Status: early development.** The current code provides small domain models and extension protocols. It is not yet a production RAG or agent framework, and its public API may change.

## What we are building

- **RAG first:** clear interfaces for retrieval, reranking, context construction, and generation.
- **Agents that compose:** tools and agent workflows that can use the same retrieval components.
- **Useful defaults, replaceable parts:** work with different models, vector stores, and data sources without locking users into one vendor.
- **Reliability over demos:** make behavior testable, observable, secure, and understandable before adding more abstractions.

## Start here

Requirements: Python 3.11 or newer. From a checkout, install the development dependencies and run the tests:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

The first domain types are deliberately lightweight:

```python
from luckybrain import Document, RetrievalResult

document = Document(
    id="guide-1",
    content="A source passage to retrieve.",
    metadata={"source": "guide.md"},
)
result = RetrievalResult(document=document, score=0.92)
```

The interfaces in `luckybrain.rag` and `luckybrain.agents` are extension points, not bundled model or database integrations. Integrations and end-to-end pipelines will be added with tests and documented behavior.

## Project map

```text
src/luckybrain/
  core/       Shared domain types
  rag/        Retrieval and generation contracts
  agents/     Agent tool contracts
tests/        Automated tests
docs/         Architecture and roadmap
```

See [Architecture](docs/architecture.md), [Roadmap](docs/roadmap.md), and [Contributing](CONTRIBUTING.md) to help shape the project.

## Project principles

1. Keep core interfaces small, typed, and independent of specific providers.
2. Make advanced behavior explicit and measurable; do not hide retrieval or agent decisions behind magic defaults.
3. Treat evaluation, citations/provenance, observability, and security as core engineering concerns.
4. Prefer interoperable standards and adapters over one-off integrations.
5. Add complexity only when a real use case and tests justify it.

## License

LuckyBrain is licensed under the MIT License. See [LICENSE](LICENSE).