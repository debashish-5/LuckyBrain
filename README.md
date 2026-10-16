# LuckyBrain

**Open, composable foundations for building AI systems.**

LuckyBrain is an early-stage Python project exploring the building blocks behind
retrieval-augmented generation (RAG), agents, multimodal applications, and the
systems that connect them. It aims to make components understandable,
replaceable, testable, and safer to build with—without tying the project to one
provider or one fixed architecture.

> **Project status: alpha.** Today the package contains lightweight domain
> models, extension protocols, and synchronous OpenAI and Groq chat clients.
> Complete RAG, agent, and multimodal pipelines are not implemented. APIs and
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

## Try the current package

Requires Python 3.11 or newer. Install the package and its development tools,
then run the tests:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```


The package also includes synchronous OpenAI and Groq chat clients. They make
provider API calls; the example above does not perform retrieval or generate an
answer. See the [Provider chat clients guide](docs/provider-clients.md) for
setup and usage. Keep API keys out of source code and use environment variables
or a secret manager.

## A flexible project, not a fixed folder map

The current layout is a starting point, not a rule that every contribution must
fit an existing directory:

```text
src/luckybrain/   Python package and current extension points
tests/            Automated tests
docs/             Architecture, provider guide, and roadmap
```

Contributors can propose new packages, folders, capabilities, integrations, or
documentation when they solve a clear problem. Keep boundaries understandable,
dependencies intentional, and additions covered by tests. See
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
