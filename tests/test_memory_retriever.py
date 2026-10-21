import asyncio
import math
from collections.abc import Sequence

import pytest

from luckybrain import Document
from luckybrain.rag import MemoryVectorRetriever


class FakeEmbedder:
    vectors = {
        "cats": [1.0, 0.0],
        "dogs": [0.0, 1.0],
        "pets": [0.8, 0.2],
    }

    def __init__(self) -> None:
        self.bad_document_count = False
        self.invalid_vector = False

    async def embed_documents(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        if self.bad_document_count:
            return []
        if self.invalid_vector:
            return [[math.nan, 0.0] for _ in texts]
        return [self.vectors[text] for text in texts]

    async def embed_query(self, text: str) -> Sequence[float]:
        return self.vectors[text]


def test_memory_retriever_ranks_and_limits_results() -> None:
    async def exercise() -> None:
        retriever = MemoryVectorRetriever(FakeEmbedder())
        documents = [
            Document(id="cats", content="cats", metadata={"source": "a"}),
            Document(id="dogs", content="dogs"),
            Document(id="pets", content="pets"),
        ]

        await retriever.add_documents(documents)
        results = await retriever.retrieve("cats", top_k=2)

        assert [result.document.id for result in results] == ["cats", "pets"]
        assert results[0].score == pytest.approx(1.0)
        assert results[1].score == pytest.approx(0.9701425)
        assert results[0].document.metadata == {"source": "a"}

    asyncio.run(exercise())


def test_memory_retriever_replaces_duplicate_ids_without_changing_order() -> None:
    async def exercise() -> None:
        retriever = MemoryVectorRetriever(FakeEmbedder())
        first = Document(id="same", content="cats")
        second = Document(id="other", content="dogs")
        replacement = Document(id="same", content="pets")

        await retriever.add_documents([first, second])
        await retriever.add_documents([replacement])

        assert len(retriever) == 2
        results = await retriever.retrieve("pets")
        assert [result.document.id for result in results] == ["same", "other"]
        assert results[0].document is replacement

    asyncio.run(exercise())


def test_memory_retriever_does_not_store_partial_invalid_batches() -> None:
    async def exercise() -> None:
        embedder = FakeEmbedder()
        retriever = MemoryVectorRetriever(embedder)
        await retriever.add_documents([Document(id="valid", content="cats")])

        embedder.invalid_vector = True
        with pytest.raises(ValueError, match="finite values"):
            await retriever.add_documents([Document(id="invalid", content="dogs")])

        assert len(retriever) == 1

    asyncio.run(exercise())


def test_memory_retriever_validates_embedder_outputs_and_queries() -> None:
    async def exercise() -> None:
        embedder = FakeEmbedder()
        retriever = MemoryVectorRetriever(embedder)
        embedder.bad_document_count = True
        with pytest.raises(ValueError, match="one vector"):
            await retriever.add_documents([Document(id="doc", content="cats")])

        embedder.bad_document_count = False
        await retriever.add_documents([Document(id="doc", content="cats")])
        with pytest.raises(ValueError, match="Query"):
            await retriever.retrieve(" ")
        with pytest.raises(ValueError, match="top_k"):
            await retriever.retrieve("cats", top_k=0)

    asyncio.run(exercise())
