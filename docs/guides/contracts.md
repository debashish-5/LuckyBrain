# RAG and agent contracts

The RAG and agent modules define Python `Protocol` interfaces. They describe
what application-owned adapters should provide; LuckyBrain does not currently
include retrievers, rerankers, generators, agent runners, or built-in tools.

## RAG

Import the contracts from `luckybrain.rag`:

```python
from collections.abc import Sequence

from luckybrain import Document, RetrievalResult
from luckybrain.rag import Generator, Reranker, Retriever


class InMemoryRetriever:
    async def retrieve(self, query: str, *, top_k: int = 10) -> Sequence[RetrievalResult]:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        document = Document(id="example", content=f"Matched: {query}")
        return [RetrievalResult(document=document, score=1.0)][:top_k]
```

`Retriever.retrieve(query, *, top_k=10)` returns ranked
`RetrievalResult` objects. `Reranker.rerank(query, results)` returns candidates
in a new or existing order. `Generator.generate(prompt)` returns generated
text. All three methods are asynchronous; the caller chooses how to connect
them, apply limits, handle errors, and assemble context.

## Agent tools

Implement `AgentTool` from `luckybrain.agents` with `name`, `description`, and
an async `invoke(inputs)` method. This belongs to the separate agent-tool
contract; chat models use `think()` for model responses. Inputs are a
`Mapping[str, object]`; the protocol does not define a schema, authorization,
approval flow, timeout, or execution engine. Validate inputs and constrain
side effects in your adapter.

## Data types

`Document` requires a non-empty ID and non-empty text content. `metadata`
defaults to a new empty mapping. `RetrievalResult` pairs a document with a
provider-defined relevance score; the score is not currently range-checked.

These interfaces are intentionally minimal, not complete production pipelines.
See their [generated API documentation](../api-reference.md) for signatures.
