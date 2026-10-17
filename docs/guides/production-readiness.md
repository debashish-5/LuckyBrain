# Production readiness

LuckyBrain is alpha software. Its current APIs are useful foundations, not a
claim that an application built on them is secure, reliable, compliant, or
production-ready by default. Your application remains responsible for these
controls.

## What the library currently does

- Validates basic text prompts and several chat-model configuration values.
- Wraps synchronous OpenAI and Groq chat-completions calls and propagates SDK
  errors.
- Defines minimal document, retrieval result, RAG, and tool contracts.
- Provides an experimental model-backed query-rewriting helper.

## What it does not provide

- A RAG pipeline, database, vector store, embedding model, orchestration loop,
  tool executor, or durable conversation store.
- Shared timeout, retry, backoff, rate-limit, concurrency, or cancellation
  management across provider calls.
- Authentication or authorization for application users; per-user isolation;
  retention or deletion controls.
- Prompt-injection defenses, output moderation, citation verification, or
  guarantees of factual accuracy.
- A stable compatibility policy, production SLA, or guarantee that provider
  model IDs and options remain available.

## Before deployment

1. Keep provider keys in a managed secret store. Rotate them, scope access, and
   never expose them to browsers or logs.
2. Decide what prompt and document data may leave your system. Review each
   provider's retention, region, training, and contractual terms.
3. Set request deadlines, bounded retries with jitter, concurrency and token
   budgets, and graceful handling for provider outages at your application
   boundary.
4. Treat prompts, retrieved text, tool inputs, and model output as untrusted.
   Validate structured inputs and independently authorize consequential
   actions.
5. Add tests, quality evaluation, monitoring, cost tracking, and a fallback
   plan for the exact models and data you use.
6. Pin and review dependency versions; test upgrades and breaking provider
   changes in staging before production rollout.

This checklist is guidance, not a security certification. Report suspected
vulnerabilities using the project's [security policy](../security.md).
