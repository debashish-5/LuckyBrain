# Architecture

LuckyBrain is intended to support composable AI systems, not prescribe a
single pipeline or directory structure. RAG is one important use case alongside
agents, multimodal applications, model and data integrations, evaluation, and
the operational controls that make these systems dependable.

## Current implementation

The package is at an early stage. It currently includes:

- Provider-neutral `Document` and `RetrievalResult` domain models.
- Source-aware character chunking and citation-aware context assembly.
- Optional local Sentence Transformers embeddings, a JSON/NumPy file-backed
  embedding index, and an async adapter for embedding models.
- An in-memory cosine-similarity retriever that consumes the async embedder
  contract.
- Asynchronous extension protocols for text retrieval, reranking, and
  generation in `luckybrain.rag`.
- An asynchronous tool contract in `luckybrain.agents`.
- Synchronous OpenAI and Groq chat clients in `luckybrain.core.models`.
- An experimental model-backed query rewriting helper in
  `luckybrain.query_imp.queryimproval`.

These pieces are not a complete connected application pipeline. The in-memory
retriever and local embedding index are prototype-scale, process/local-file
components rather than durable databases. The chat clients do not perform
retrieval, multimodal processing, or agent orchestration. See the [chat models
guide](guides/chat-models.md), [embedding guide](guides/embeddings.md),
[query rewriting guide](guides/query-rewriting.md), and [API
reference](api-reference.md) for current behavior and boundaries.

## Composable system lifecycle

A future application may connect stages such as:

**Inputs and sources** → **validation and parsing** → **task-specific
processing** → **representations and storage** → **retrieval or selection** →
**orchestration and context** → **model or tool execution** → **outputs and
provenance** → **evaluation and observability**

This is a map of concerns, not a required sequence or implemented pipeline.
Applications may omit, repeat, combine, or reorder stages. A text search
application, for example, need not use agents; an audio workflow may need
transcription before retrieval; and an agent may call a tool without RAG.
Implementations should keep boundaries explicit so components can be tested
and replaced independently.

## Capability areas

These are possible areas of the architecture, not required top-level folders:

- **Knowledge and retrieval:** connectors, parsing, chunking, embeddings,
  indexes, search, reranking, context assembly, citations, and evaluation.
- **Multimodal:** image, audio, video, and mixed-media input/output, including
  extraction, transformation, indexing, and retrieval.
- **Agents and tools:** orchestration, tool schemas, state, memory, permissions,
  timeouts, and human approval.
- **Models and infrastructure:** provider adapters, local inference, storage,
  caching, queues, and deployment.
- **Cross-cutting quality:** testing, reproducibility, tracing, cost and latency
  measurement, privacy, and security.

Contributors can correct or improve existing behavior and add new modules,
subpackages, integrations, or capabilities within `src/luckybrain/`. The
current folders are a starting point, not a restriction. Give new code a clear
responsibility, keep shared interfaces provider-neutral where practical, avoid
unnecessary dependencies in core, and explain important trade-offs in the
contribution or design proposal.

## Design constraints

- Keep integrations behind typed, testable boundaries; avoid leaking vendor SDK
  types into shared contracts.
- Make synchronous and asynchronous behavior, errors, retries, and resource
  limits explicit.
- Preserve source identity and provenance where transformations or generated
  outputs depend on source material.
- Treat external content, provider responses, and tool inputs as untrusted.
- Make model, retrieval, and tool decisions inspectable; avoid hidden network
  calls and unbounded side effects.
- Test with deterministic fakes. Keep live-provider tests opt-in and do not
  require secrets for the normal test suite.
- Document what is implemented, what is experimental, and what is only
  proposed. Make compatibility promises deliberately as public APIs mature.

## Security and privacy boundaries

AI systems can expose data or take unintended actions even when individual
components work as designed. Architecture and integrations should account for:

- **Credential protection:** read secrets from approved secret stores or
  environment configuration; never log, return, or commit them.
- **Data handling:** minimize what is sent to providers, define retention and
  deletion behavior, and avoid exposing sensitive prompts or content in logs,
  traces, fixtures, and examples.
- **Untrusted inputs:** validate documents, URLs, media, and structured tool
  arguments; consider prompt injection, malicious files, parser limits, and
  resource exhaustion.
- **Constrained actions:** give tools least privilege, set timeouts and
  resource limits, and require explicit approval for consequential actions.
- **Supply chain:** keep dependencies purposeful and maintained, and review
  provider and storage integrations as part of the trust boundary.

These are design requirements to build toward, not guarantees provided by the
current alpha package. See the [security page](security.md) for reporting
suspected vulnerabilities.
