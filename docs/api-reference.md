# API reference

This reference is generated from the Python source on every documentation build.
Signatures and source docstrings stay connected to the implementation; use the
guides for complete examples, parameter explanations, and operational advice.

## Public data models

::: luckybrain.core.models.Document

::: luckybrain.core.models.RetrievalResult

## Chat models

::: luckybrain.core.models.ChatMessage

::: luckybrain.core.models.ChatInput

::: luckybrain.core.models.BaseChatModel

::: luckybrain.core.models.ChatModelProtocol

::: luckybrain.core.models.OpenaiBrain

::: luckybrain.core.models.GroqBrain

## Retrieval and generation protocols

::: luckybrain.rag.chunking.DocumentChunker

::: luckybrain.rag.memory.MemoryVectorRetriever

::: luckybrain.rag.protocols.Retriever

::: luckybrain.rag.protocols.VectorEmbedder

::: luckybrain.rag.protocols.VectorStore

::: luckybrain.rag.protocols.Reranker

::: luckybrain.rag.protocols.Generator

## Agent tools

::: luckybrain.agents.protocols.AgentTool

## Query rewriting

`QueryRewriting` is experimental and available from `luckybrain.query_imp`;
it is not re-exported from the package root.

::: luckybrain.query_imp.queryimproval.QueryRewriting

## Re-exported names

The package root exports `Document` and `RetrievalResult`. The `luckybrain.rag`
module exports `Retriever`, `Reranker`, and `Generator`; `luckybrain.agents`
exports `AgentTool`. Provider clients and experimental query rewriting must be
imported from the module paths shown above.
