# Roadmap

This roadmap records direction, not delivery promises. Issues and design discussions should refine priorities around real user needs.

## Foundation

- [x] Establish the Python package, domain types, contributor guidance, and CI checks.
- [ ] Agree on compatibility and release policy after the first usable APIs settle.
- [ ] Add structured error types and shared configuration conventions where required by real components.

## RAG

- [x] Add source-aware character chunking and in-memory cosine retrieval with
  async embedder and vector-store contracts.
- [ ] Define ingestion, chunking, embedding, and vector-store adapter contracts for durable integrations.
- [ ] Build a full composable retrieval pipeline with deterministic test adapters.
- [ ] Preserve document identity, metadata, and citations through context assembly and answers.
- [ ] Add evaluation datasets and repeatable retrieval and answer-quality metrics.
- [ ] Add optional adapters for commonly used storage and model providers.

## Agents

- [ ] Define explicit tool input/output, timeout, and failure contracts.
- [ ] Compose agents with retrieval without making a specific orchestration vendor mandatory.
- [ ] Add safeguards, traceability, and reproducible tests for tool execution.

## Multimodal and integrations

- [ ] Explore provider-neutral contracts for image, audio, video, and mixed-media inputs and outputs.
- [ ] Define how media validation, parsing, representations, and provenance fit with retrieval and generation.
- [ ] Add integrations as optional adapters with documented data handling and failure behavior.

## Quality and community

- [ ] Publish design proposals for major public abstractions.
- [ ] Add examples only when they exercise supported APIs end to end.
- [ ] Establish repeatable quality, latency, and cost evaluation for supported components.
- [ ] Document security, privacy, retention, and permission behavior for each integration before recommending production use.