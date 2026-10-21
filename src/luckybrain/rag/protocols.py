"""Provider-neutral asynchronous RAG extension protocols."""

from collections.abc import Sequence
from typing import Protocol

from luckybrain.core.models import Document, RetrievalResult


class Retriever(Protocol):
    """Retrieve ranked source documents for a text query."""

    async def retrieve(self, query: str, *, top_k: int = 10) -> Sequence[RetrievalResult]: ...


class VectorEmbedder(Protocol):
    """Create vectors for document text and search queries."""

    async def embed_documents(self, texts: Sequence[str]) -> Sequence[Sequence[float]]: ...

    async def embed_query(self, text: str) -> Sequence[float]: ...


class VectorStore(Protocol):
    """Store documents and retrieve them by vector similarity."""

    async def add_documents(self, documents: Sequence[Document]) -> None: ...

    async def retrieve(self, query: str, *, top_k: int = 10) -> Sequence[RetrievalResult]: ...


class Reranker(Protocol):
    """Reorder candidate documents for a text query."""

    async def rerank(
        self, query: str, results: Sequence[RetrievalResult]
    ) -> Sequence[RetrievalResult]: ...


class Generator(Protocol):
    """Generate text from a prompt assembled by a calling component."""

    async def generate(self, prompt: str) -> str: ...
