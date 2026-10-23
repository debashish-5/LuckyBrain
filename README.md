<div align="center">
  <img src="docs/assets/favicon.svg" alt="LuckyBrain logo" width="104">
  <h1>LuckyBrain</h1>
  <p><strong>Open, composable foundations for building AI systems.</strong></p>
  <p>
    <a href="https://debashish-5.github.io/LuckyBrain/">Website</a> ·
    <a href="docs/index.md">Documentation</a> ·
    <a href="docs/api-reference.md">API reference</a> ·
    <a href="docs/connect.md">Connect</a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/status-alpha-f0b429?style=flat-square" alt="Project status: alpha">
    <img src="https://img.shields.io/badge/python-3.11%2B-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python 3.11 or newer">
    <img src="https://img.shields.io/badge/license-MIT-91c85a?style=flat-square" alt="MIT license">
  </p>
</div>

LuckyBrain is an early-stage Python project exploring the building blocks behind
retrieval-augmented generation (RAG), agents, multimodal applications, and the
systems that connect them. The goal: make components understandable,
replaceable, testable, and safer to build with—without locking you into one
provider or one fixed architecture.

> [!IMPORTANT]
> **LuckyBrain is alpha software.** The package currently provides lightweight
> domain models, source-aware text chunking, citation context assembly,
> in-memory vector retrieval, optional local embeddings, asynchronous agent/RAG
> protocols, synchronous OpenAI and Groq chat clients, and experimental query
> rewriting. A complete RAG pipeline, durable vector database, agent runner,
> and multimodal pipeline are **not** implemented. APIs and architecture may
> change as the project develops.

## See LuckyBrain

<div align="center">
  <video src="https://debashish-5.github.io/LuckyBrain/video_for_readme/ascii-magic-1.mp4" controls preload="metadata" width="100%">
    Your browser does not support embedded video.
  </video>
</div>

## Get started

Requires **Python 3.11 or newer**. Install LuckyBrain with its development
tools, then run the test suite:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

### Optional local embeddings

Install the embeddings extra to use local text embeddings and a small
cosine-similarity index:

```bash
python -m pip install -e ".[embeddings]"
```

See the [embedding guide](docs/guides/embeddings.md) for model setup and an
example connecting embeddings to the asynchronous in-memory retriever.

## What you can build with

AI applications are more than a single RAG pipeline. LuckyBrain is open to
well-scoped contributions across the full lifecycle:

| Area | Examples |
| --- | --- |
| **Knowledge and retrieval** | Data connectors, parsing, chunking, embeddings, indexes, search, reranking, citations, and evaluation |
| **Multimodal systems** | Image, audio, video, and mixed-media inputs; extraction, representations, retrieval, and generated outputs |
| **Agents and tools** | Tool contracts, orchestration, memory, state, permissions, and human approval |
| **Models and integrations** | Provider adapters, local models, storage backends, and interoperability |
| **Quality and operations** | Testing, benchmarks, tracing, observability, privacy, security, and deployment guidance |

These are areas to explore, not a promise that the capabilities already exist.
See [Architecture](docs/architecture.md) for current boundaries and design
principles, and the [Roadmap](docs/roadmap.md) for ideas under consideration.

## A small example

LuckyBrain includes a lightweight prompt templating helper for string-based
model prompts:

```python
from luckybrain.prompts import PromptFormat

prompt = PromptFormat(
    "You are helping {role}. Summarize the key points for {audience}."
)

filled = prompt.format(role="researcher", audience="engineering leadership")
print(filled)

partial = prompt.partial(role="researcher")
print(partial.format(audience="engineering leadership"))
```

`PromptFormat` validates required variables before formatting, supports
`partial()` to fix values ahead of time, and can call a chat model directly via
`think()`. Read the [prompt templating guide](docs/guides/prompt-formatting.md)
for full examples.

### Models and query rewriting

The synchronous OpenAI and Groq chat clients make provider API calls; the
prompt example above does not perform retrieval or generate an answer. See the
[chat models guide](docs/guides/chat-models.md) for setup and usage. Keep API
keys out of source code; use environment variables or a secret manager.

The experimental [query rewriting helper](docs/guides/query-rewriting.md)
accepts an existing synchronous chat model. It does not perform retrieval.

## Explore the project

The [LuckyBrain website](https://debashish-5.github.io/LuckyBrain/) includes
responsive guides and a Python API reference generated from source docstrings.
Every public feature should ship with both source documentation and a user
guide; see the [contributor documentation](docs/contributing.md).

To preview the documentation site locally:

```powershell
python -m pip install -e ".[docs]"
python -m mkdocs serve
```

The CI documentation workflow validates changes and publishes updates from
`main` to GitHub Pages. The repository's Pages source must be set to
**GitHub Actions** for the hosted site to deploy.

```text
src/luckybrain/   Python package and current extension points
tests/            Automated tests
docs/             Architecture, guides, API reference, and roadmap
```

This layout is a starting point, not a rule. Contributors can improve any part
of the project and add modules inside `src/luckybrain/`. Keep boundaries
understandable, dependencies intentional, and changes covered by tests.

## Project principles

- **Composable:** small, typed, independently replaceable components.
- **Provider-neutral:** integrations are adapters, not architectural
  requirements.
- **Observable and evaluable:** decisions, failures, provenance, and quality
  should be measurable.
- **Secure and privacy-aware:** prompts, documents, media, credentials, model
  responses, and tools are trust boundaries.
- **Evidence-led:** distinguish implemented behavior from proposals and prefer
  tested use cases over speculative abstractions.

## Contribute

Questions, bug reports, tests, documentation, design proposals, and new
capabilities are welcome. Start with [Contributing](CONTRIBUTING.md), and
follow the community standards in [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

LuckyBrain is alpha software, not a security certification. Do not use real
credentials, private data, or sensitive production workloads without reviewing
the code and every integration you use. For reporting vulnerabilities, see the
[Security Policy](SECURITY.md).

## License

LuckyBrain is licensed under the MIT License. See [LICENSE](LICENSE) and the
contribution guide's [copyright and attribution notes](CONTRIBUTING.md#copyright-license-and-attribution)
for details.
