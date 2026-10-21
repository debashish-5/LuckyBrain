# LuckyBrain

**Open, composable foundations for building AI systems.**

[Project website](https://debashish-5.github.io/LuckyBrain/) ·
[Documentation](docs/index.md) ·
[API reference](docs/api-reference.md) ·
[Connect](docs/connect.md)

LuckyBrain is an early-stage Python project exploring the building blocks behind
retrieval-augmented generation (RAG), agents, multimodal applications, and the
systems that connect them. It aims to make components understandable,
replaceable, testable, and safer to build with—without tying the project to one
provider or one fixed architecture.

> **Project status: alpha.** Today the package contains lightweight domain
> models, source-aware text chunking, a citation context builder, in-memory
> vector retrieval, optional local embeddings, asynchronous agent/RAG
> protocols, synchronous OpenAI and Groq chat clients, and an experimental
> query-rewriting helper. A complete RAG pipeline, durable vector database,
> agent runner, and multimodal pipeline are not implemented. APIs and
> architecture may change as the project develops.

## What belongs here?

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
See [Architecture](docs/architecture.md) for design principles and current
boundaries, and the [Roadmap](docs/roadmap.md) for ideas under consideration.

The [LuckyBrain website](https://debashish-5.github.io/LuckyBrain/) includes
responsive guides and a Python API reference generated from the source
docstrings. Every public feature should ship with both source documentation
and a user guide; see the [contributor documentation](docs/contributing.md).

To preview the documentation site while working on it:

```powershell
python -m pip install -e ".[docs]"
python -m mkdocs serve
```

The CI documentation workflow validates every change and publishes updates
from `main` to GitHub Pages. The repository's Pages source must be set to
**GitHub Actions** for the hosted site to be deployed.

## Try the current package

Requires Python 3.11 or newer. Install the package and its development tools,
then run the tests:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```


The package also includes synchronous OpenAI and Groq chat clients. They make
provider API calls; the example above does not perform retrieval or generate an
answer. See the [chat models guide](docs/guides/chat-models.md) for setup and
usage. Keep API keys out of source code and use environment variables or a
secret manager.

The project also includes a lightweight prompt templating helper for
string-based model prompts:

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
`think()`. See the [prompt templating guide](docs/guides/prompt-formatting.md)
for full usage examples.

The experimental [query rewriting helper](docs/guides/query-rewriting.md)
accepts an existing synchronous chat model; it does not perform retrieval.

Optional local text embeddings and a small cosine-similarity index are
available with `python -m pip install -e ".[embeddings]"`. See the
[embedding guide](docs/guides/embeddings.md) for model setup and a complete
connection to the asynchronous in-memory retriever.

## A flexible project, not a fixed folder map

The current layout is a starting point, not a rule that every contribution must
fit an existing directory:

```text
src/luckybrain/   Python package and current extension points
tests/            Automated tests
docs/             Architecture, provider guide, and roadmap
```

Contributors can fix or improve anything in the project, and can add new modules
and subpackages inside `src/luckybrain/`—they do not have to limit work to the
existing folders or roadmap. Keep boundaries understandable, dependencies
intentional, and changes covered by tests. Contributions are submitted as pull
requests for review. See
[Contributing](CONTRIBUTING.md) for how to shape and submit changes.

## Principles

- **Composable:** keep components small, typed, and independently replaceable.
- **Provider-neutral:** make integrations adapters rather than architectural
  requirements.
- **Observable and evaluable:** make decisions, failures, provenance, and
  quality measurable.
- **Secure and privacy-aware:** treat prompts, documents, media, credentials,
  model responses, and tools as trust boundaries.
- **Evidence-led:** distinguish implemented behavior from proposals, and prefer
  tested use cases over speculative abstractions.

## Security

LuckyBrain is alpha software, not a security certification. Do not put real
credentials, private data, or sensitive production workloads through it
without reviewing the code and every integration you use. For reporting
vulnerabilities, see [Security Policy](SECURITY.md).

## Contribute

Questions, bug reports, tests, documentation, design proposals, and new
capabilities are welcome. Start with [Contributing](CONTRIBUTING.md), and follow
the community standards in [Code of Conduct](CODE_OF_CONDUCT.md).

## License

LuckyBrain is licensed under the MIT License. This allows reuse and forks,
including commercial derivatives, provided the required license and copyright
notices are retained; it does not prevent others from building a competing
project from the code. See [LICENSE](LICENSE) and the contribution guide's
[copyright and attribution notes](CONTRIBUTING.md#copyright-license-and-attribution)
for details.
