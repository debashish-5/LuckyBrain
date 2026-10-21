"""In-memory vector retrieval for small datasets and deterministic tests."""

from collections.abc import Sequence
from math import fsum, isfinite, sqrt

from luckybrain.core.models import Document, RetrievalResult
from luckybrain.rag.protocols import VectorEmbedder


class MemoryVectorRetriever:
    """Retrieve documents by cosine similarity using an asynchronous embedder.

    This implementation keeps both documents and vectors in process memory.
    It is useful for tests, prototypes, and small datasets, but is not durable
    storage and does not provide concurrent-writer coordination.
    """

    def __init__(self, embedder: VectorEmbedder) -> None:
        self._embedder = embedder
        self._entries: dict[str, tuple[Document, tuple[float, ...], float]] = {}

    def __len__(self) -> int:
        return len(self._entries)

    async def add_documents(self, documents: Sequence[Document]) -> None:
        """Embed and add documents, replacing any existing entry with the same ID."""
        if not documents:
            return

        vectors = await self._embedder.embed_documents([document.content for document in documents])
        if len(vectors) != len(documents):
            raise ValueError("Embedder must return one vector for each document.")

        staged: list[tuple[Document, tuple[float, ...], float]] = []
        expected_dimension = (
            len(next(iter(self._entries.values()))[1]) if self._entries else None
        )
        for document, vector in zip(documents, vectors, strict=True):
            values = tuple(float(value) for value in vector)
            if not values or any(not isfinite(value) for value in values):
                raise ValueError("Document vectors must contain finite values.")
            if expected_dimension is None:
                expected_dimension = len(values)
            elif len(values) != expected_dimension:
                raise ValueError("All document vectors must have the same dimension.")
            norm = sqrt(fsum(value * value for value in values))
            staged.append((document, values, norm))

        updates = {
            document.id: (document, vector, norm)
            for document, vector, norm in staged
        }
        self._entries.update(updates)

    async def retrieve(self, query: str, *, top_k: int = 10) -> Sequence[RetrievalResult]:
        """Return the highest-scoring documents, preserving insertion order for ties."""
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must not be empty.")
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer.")
        if not self._entries:
            return []

        query_vector = tuple(float(value) for value in await self._embedder.embed_query(query))
        if not query_vector or any(not isfinite(value) for value in query_vector):
            raise ValueError("Query vector must contain finite values.")

        first_document = next(iter(self._entries.values()))[1]
        if len(query_vector) != len(first_document):
            raise ValueError("Query and document vectors must have the same dimension.")

        query_norm = sqrt(fsum(value * value for value in query_vector))
        results: list[RetrievalResult] = []
        for document, vector, document_norm in self._entries.values():
            denominator = query_norm * document_norm
            score = (
                fsum(query_value * document_value for query_value, document_value in zip(
                    query_vector, vector, strict=True
                ))
                / denominator
                if denominator
                else 0.0
            )
            results.append(RetrievalResult(document=document, score=score))

        results.sort(key=lambda result: result.score, reverse=True)
        return results[:top_k]
