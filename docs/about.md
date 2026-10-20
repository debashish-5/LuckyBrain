# About LuckyBrain

LuckyBrain is an open-source Python project exploring the foundations behind
retrieval-augmented generation, agents, and the systems that connect them.
Its goal is to make components understandable, replaceable, testable, and
safer to build with—not to hide application decisions behind one fixed
framework.

## What exists today

The package is at an early stage. Current code includes small domain models,
synchronous OpenAI and Groq chat clients, a lightweight prompt templating
helper, a model-backed query rewriting helper, and asynchronous protocols for
RAG and agent-tool integrations. The protocols are contracts only: complete
retrieval and agent pipelines are not included.

## Project principles

- **Composable:** keep components small and replaceable.
- **Provider-aware:** isolate integrations behind explicit adapters.
- **Inspectable:** make behavior, errors, limitations, and trade-offs clear.
- **Evidence-led:** distinguish implemented functionality from future ideas.
- **Responsible:** consider privacy, security, and operational controls from
  the beginning.

LuckyBrain is maintained in the open. Read the [architecture](architecture.md)
and [roadmap](roadmap.md), or [connect with the project](connect.md).
