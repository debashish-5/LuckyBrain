# Architecture

## Boundaries

- `core`: shared domain models and contracts. `Document` and `RetrievalResult` are provider-neutral. The current `core.models` module also contains direct OpenAI and Groq chat clients; these require their respective SDKs.
- `rag`: retrieval, reranking, context assembly, generation, and evaluation components.
- `agents`: tools and agent workflows that can compose RAG components.
- Future integrations: provider-specific adapters, grouped by capability or provider as the codebase grows.

The current implementation includes initial domain models, protocols, and basic OpenAI/Groq chat clients. The directory boundaries are a guide, not a promise that every planned subsystem already exists. See the [Provider chat clients guide](provider-clients.md) for their usage and API.

## Design constraints

- Define typed contracts at integration boundaries; keep vendor SDK types out of core APIs.
- Make asynchronous behavior and error handling explicit.
- Preserve source identity and provenance through retrieval and generation workflows.
- Make configuration, ranking, and agent decisions inspectable; avoid hidden network calls.
- Test components with deterministic fakes. Keep live-provider tests opt-in.
- Add compatibility guarantees only after the API has enough real use to justify them.

## Proposed RAG flow

Ingestion and parsing -> chunking -> embedding and indexing -> retrieval -> optional reranking -> context assembly -> generation -> citations and evaluation.

This is a conceptual flow, not an implemented pipeline. Each stage should remain independently replaceable and observable.