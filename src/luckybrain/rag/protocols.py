"""Provider-neutral asynchronous RAG extension protocols."""

from collections.abc import Sequence
from typing import Protocol

from luckybrain.core.models import RetrievalResult


class Retriever(Protocol):
    """Retrieve ranked source documents for a text query."""

    async def retrieve(self, query: str, *, top_k: int = 10) -> Sequence[RetrievalResult]: ...


class Reranker(Protocol):
    """Reorder candidate documents for a text query."""

    async def rerank(
        self, query: str, results: Sequence[RetrievalResult]
    ) -> Sequence[RetrievalResult]: ...


class Generator(Protocol):
    """Generate text from a prompt assembled by a calling component."""

    async def generate(self, prompt: str) -> str: ...
