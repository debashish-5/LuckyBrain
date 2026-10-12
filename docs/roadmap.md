# Roadmap

This roadmap records direction, not delivery promises. Issues and design discussions should refine priorities around real user needs.

## Foundation

- [x] Establish the Python package, domain types, contributor guidance, and CI checks.
- [ ] Agree on compatibility and release policy after the first usable APIs settle.
- [ ] Add structured error types and shared configuration conventions where required by real components.

## RAG

- [ ] Define ingestion, chunking, embedding, and vector-store adapter contracts.
- [ ] Build a minimal composable retrieval pipeline with deterministic test adapters.
- [ ] Preserve document identity, metadata, and citations through context assembly and answers.
- [ ] Add evaluation datasets and repeatable retrieval and answer-quality metrics.
- [ ] Add optional adapters for commonly used storage and model providers.

## Agents

- [ ] Define explicit tool input/output, timeout, and failure contracts.
- [ ] Compose agents with retrieval without making a specific orchestration vendor mandatory.
- [ ] Add safeguards, traceability, and reproducible tests for tool execution.

## Quality and community

- [ ] Publish design proposals for major public abstractions.
- [ ] Add examples only when they exercise supported APIs end to end.
- [ ] Document security and privacy behavior for each integration before recommending production use.