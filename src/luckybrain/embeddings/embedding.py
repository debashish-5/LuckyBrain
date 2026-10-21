"""Text embedding models, asynchronous adapters, and a small local index."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping, Sequence
from math import isfinite
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast

if TYPE_CHECKING:
    from numpy import float32
    from numpy.typing import NDArray


def _numpy() -> Any:
    try:
        import numpy as np
    except ImportError as error:
        raise ImportError(
            "Text embeddings and indexes require NumPy. "
            "Install it with `pip install luckybrain[embeddings]`."
        ) from error
    return np


class _SentenceEncoder(Protocol):
    def get_embedding_dimension(self) -> int: ...

    def encode(
        self,
        sentences: list[str],
        *,
        batch_size: int,
        normalize_embeddings: bool,
        show_progress_bar: bool,
        convert_to_numpy: bool,
    ) -> object: ...


class Embedding(Protocol):
    """Synchronous interface for embedding text."""

    def embedding_documents(
        self, texts: Sequence[str], show_progress: bool = False
    ) -> NDArray[float32]:
        """Return one embedding vector for each input document."""
        ...

    def embed_query(self, text: str) -> NDArray[float32]:
        """Return an embedding vector for a search query."""
        ...


class HFEmbedder:
    """Create normalized text embeddings with a Sentence Transformers model.

    Install the optional dependencies with ``pip install luckybrain[embeddings]``.
    The model is loaded locally when this class is instantiated; a model may
    download weights on first use according to the Hugging Face cache settings.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str | None = None,
        normalize: bool = True,
        batch_size: int = 32,
        query_prefix: str = "",
        doc_prefix: str = "",
    ) -> None:
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("model_name must not be empty.")
        if device is not None and (not isinstance(device, str) or not device.strip()):
            raise ValueError("device must be a non-empty device name or None.")
        if not isinstance(normalize, bool):
            raise ValueError("normalize must be a boolean.")
        if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size < 1:
            raise ValueError("batch_size must be a positive integer.")
        if not isinstance(query_prefix, str) or not isinstance(doc_prefix, str):
            raise ValueError("query_prefix and doc_prefix must be strings.")

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise ImportError(
                "HFEmbedder requires Sentence Transformers. "
                "Install it with `pip install luckybrain[embeddings]`."
            ) from error

        self.model_name = model_name
        self.model: _SentenceEncoder = cast(
            _SentenceEncoder,
            SentenceTransformer(model_name, device=device),
        )
        self.normalize = normalize
        self.batch_size = batch_size
        self.query_prefix = query_prefix
        self.doc_prefix = doc_prefix

    @property
    def dimension(self) -> int:
        """Return the vector dimension reported by the loaded model."""
        return self.model.get_embedding_dimension()

    def _encode(self, texts: Sequence[str], show_progress: bool = False) -> NDArray[float32]:
        np = _numpy()
        vectors = cast(
            "NDArray[float32]",
            np.asarray(
                self.model.encode(
                    list(texts),
                    batch_size=self.batch_size,
                    normalize_embeddings=self.normalize,
                    show_progress_bar=show_progress,
                    convert_to_numpy=True,
                ),
                dtype=np.float32,
            ),
        )
        if vectors.ndim != 2 or vectors.shape != (len(texts), self.dimension):
            raise ValueError(
                "Embedding model must return a two-dimensional array with one "
                "vector per input and the configured embedding dimension."
            )
        if not np.isfinite(vectors).all():
            raise ValueError("Embedding model returned non-finite vector values.")
        return vectors

    def embedding_documents(
        self, texts: Sequence[str], show_progress: bool = False
    ) -> NDArray[float32]:
        """Return one embedding vector for each input document."""
        if any(not isinstance(text, str) for text in texts):
            raise ValueError("Document texts must all be strings.")
        if not texts:
            np = _numpy()
            return cast(
                "NDArray[float32]",
                np.empty((0, self.dimension), dtype=np.float32),
            )
        return self._encode(
            [self.doc_prefix + text for text in texts],
            show_progress=show_progress,
        )

    def embed_documents(
        self, texts: Sequence[str], show_progress: bool = False
    ) -> NDArray[float32]:
        """Alias for ``embedding_documents`` using the common embedder name."""
        return self.embedding_documents(texts, show_progress=show_progress)

    def embed_query(self, text: str) -> NDArray[float32]:
        """Return an embedding vector for a search query."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Query text must not be empty.")
        return cast("NDArray[float32]", self._encode([self.query_prefix + text])[0])

    def similarity(self, first: str, second: str) -> float:
        """Return cosine similarity between two text inputs."""
        np = _numpy()
        first_vector = self.embed_query(first)
        second_vector = self.embed_query(second)
        denominator = float(np.linalg.norm(first_vector) * np.linalg.norm(second_vector))
        if denominator == 0:
            return 0.0
        return float(np.dot(first_vector, second_vector) / denominator)


class AsyncEmbeddingAdapter:
    """Expose a synchronous embedder through the async RAG embedding protocol.

    Embedding work runs in a worker thread so model inference does not block the
    asyncio event loop.
    """

    def __init__(self, embedder: Embedding) -> None:
        self._embedder = embedder

    async def embed_documents(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        """Embed documents off the event loop and return immutable vectors."""
        vectors = await asyncio.to_thread(self._embedder.embedding_documents, texts)
        return tuple(tuple(float(value) for value in vector) for vector in vectors)

    async def embed_query(self, text: str) -> tuple[float, ...]:
        """Embed one query off the event loop and return an immutable vector."""
        vector = await asyncio.to_thread(self._embedder.embed_query, text)
        return tuple(float(value) for value in vector)


class EmbeddingIndex:
    """Store text records and search their embeddings by cosine similarity."""

    def __init__(self, embedder: Embedding) -> None:
        self.embedder = embedder
        self.items: list[dict[str, object]] = []
        self.vectors: NDArray[float32] | None = None

    def __len__(self) -> int:
        return len(self.items)

    def add(
        self,
        chunks: Sequence[Mapping[str, object]],
        show_progress: bool = True,
    ) -> None:
        """Embed non-empty ``text`` fields and append their source records."""
        items: list[dict[str, object]] = []
        for chunk in chunks:
            text = chunk.get("text")
            if not isinstance(text, str):
                raise ValueError("Each chunk must have a string 'text' field.")
            if text.strip():
                items.append(dict(chunk))
        if not items:
            return

        np = _numpy()
        vectors = np.asarray(
            self.embedder.embedding_documents(
                [item["text"] for item in items if isinstance(item["text"], str)],
                show_progress=show_progress,
            ),
            dtype=np.float32,
        )
        if vectors.ndim != 2 or vectors.shape[0] != len(items) or vectors.shape[1] < 1:
            raise ValueError("Embedder must return one non-empty vector per chunk.")
        if not np.isfinite(vectors).all():
            raise ValueError("Embedder returned non-finite vector values.")
        if self.vectors is not None and vectors.shape[1] != self.vectors.shape[1]:
            raise ValueError("New embedding vectors must match the index dimension.")

        self.items.extend(items)
        self.vectors = vectors if self.vectors is None else np.vstack((self.vectors, vectors))

    def search(
        self,
        query: str,
        k: int = 5,
        min_score: float | None = None,
    ) -> list[dict[str, object]]:
        """Return the top cosine matches, optionally filtering by a score floor."""
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must not be empty.")
        if isinstance(k, bool) or not isinstance(k, int) or k < 1:
            raise ValueError("k must be a positive integer.")
        if min_score is not None and (
            isinstance(min_score, bool)
            or not isinstance(min_score, (int, float))
            or not isfinite(min_score)
        ):
            raise ValueError("min_score must be a finite number or None.")
        if self.vectors is None:
            return []

        np = _numpy()
        query_vector = np.asarray(self.embedder.embed_query(query), dtype=np.float32)
        if query_vector.ndim != 1 or query_vector.shape[0] != self.vectors.shape[1]:
            raise ValueError("Query embedding must match the index dimension.")
        if not np.isfinite(query_vector).all():
            raise ValueError("Embedder returned non-finite query values.")

        query_norm = float(np.linalg.norm(query_vector))
        vector_norms = np.linalg.norm(self.vectors, axis=1)
        denominators = vector_norms * query_norm
        dot_products = self.vectors @ query_vector
        scores = np.divide(
            dot_products,
            denominators,
            out=np.zeros_like(dot_products),
            where=denominators != 0,
        )
        ranked_indices = np.argsort(-scores, kind="stable")

        results: list[dict[str, object]] = []
        for index in ranked_indices:
            score = float(scores[index])
            if min_score is not None and score < min_score:
                continue
            results.append({**self.items[int(index)], "score": score})
            if len(results) == k:
                break
        return results

    def save(self, folder: str | Path) -> None:
        """Save vectors and JSON-compatible source records to a directory."""
        np = _numpy()
        folder_path = Path(folder)
        folder_path.mkdir(parents=True, exist_ok=True)
        vectors = (
            self.vectors
            if self.vectors is not None
            else np.empty((0, 0), dtype=np.float32)
        )
        np.save(folder_path / "vectors.npy", vectors, allow_pickle=False)
        (folder_path / "items.json").write_text(
            json.dumps(self.items, ensure_ascii=True),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, folder: str | Path, embedder: Embedding) -> EmbeddingIndex:
        """Load a saved index without enabling NumPy object deserialization."""
        np = _numpy()
        folder_path = Path(folder)
        vectors = np.load(folder_path / "vectors.npy", allow_pickle=False)
        items = json.loads((folder_path / "items.json").read_text(encoding="utf-8"))
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise ValueError("Saved index items must be a JSON list of objects.")
        if vectors.ndim != 2 or vectors.shape[0] != len(items):
            raise ValueError("Saved vectors and items must have matching row counts.")
        if vectors.shape[1] == 0 and items:
            raise ValueError("Saved non-empty index must have non-empty vectors.")
        if not np.isfinite(vectors).all():
            raise ValueError("Saved vectors contain non-finite values.")

        index = cls(embedder)
        index.items = items
        index.vectors = np.asarray(vectors, dtype=np.float32) if items else None
        return index

    @classmethod
    def loader(cls, folder: str | Path, embedder: Embedding) -> EmbeddingIndex:
        """Compatibility alias for :meth:`load`."""
        return cls.load(folder, embedder)
