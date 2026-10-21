import asyncio
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest

from luckybrain import Document
from luckybrain.embeddings import AsyncEmbeddingAdapter, EmbeddingIndex, HFEmbedder
from luckybrain.rag import MemoryVectorRetriever


class FakeSentenceModel:
    dimension = 2

    def __init__(self) -> None:
        self.calls: list[tuple[list[str], dict[str, object]]] = []
        self.vectors = {
            "doc:alpha": [3.0, 4.0],
            "doc:beta": [0.0, 5.0],
            "doc:zero": [0.0, 0.0],
            "query:alpha": [3.0, 4.0],
            "query:beta": [0.0, 5.0],
            "query:zero": [0.0, 0.0],
        }

    def get_embedding_dimension(self) -> int:
        return self.dimension

    def encode(
        self,
        sentences: list[str],
        *,
        batch_size: int,
        normalize_embeddings: bool,
        show_progress_bar: bool,
        convert_to_numpy: bool,
    ) -> np.ndarray:
        self.calls.append(
            (
                list(sentences),
                {
                    "batch_size": batch_size,
                    "normalize_embeddings": normalize_embeddings,
                    "show_progress_bar": show_progress_bar,
                    "convert_to_numpy": convert_to_numpy,
                },
            )
        )
        return np.asarray([self.vectors[text] for text in sentences], dtype=np.float32)


def install_fake_sentence_transformer(
    monkeypatch: pytest.MonkeyPatch,
    model: FakeSentenceModel,
) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []

    def create_model(model_name: str, *, device: str | None) -> FakeSentenceModel:
        calls.append({"model_name": model_name, "device": device})
        return model

    module = ModuleType("sentence_transformers")
    module.SentenceTransformer = create_model
    monkeypatch.setitem(sys.modules, "sentence_transformers", module)
    return calls


class FakeEmbedder:
    def __init__(self) -> None:
        self.vectors = {
            "cats": [1.0, 0.0],
            "diagonal": [0.8, 0.6],
            "dogs": [0.0, 1.0],
        }
        self.bad_output = False

    def embedding_documents(
        self, texts: Sequence[str], show_progress: bool = False
    ) -> np.ndarray:
        if self.bad_output:
            return np.asarray([[np.nan, 0.0]], dtype=np.float32)
        return np.asarray([self.vectors[text] for text in texts], dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return np.asarray(self.vectors[text], dtype=np.float32)


def test_hf_embedder_applies_prefixes_and_uses_a_valid_device_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = FakeSentenceModel()
    created = install_fake_sentence_transformer(monkeypatch, model)

    embedder = HFEmbedder(query_prefix="query:", doc_prefix="doc:", batch_size=7)
    documents = embedder.embedding_documents(["alpha", "beta"], show_progress=True)
    query = embedder.embed_query("alpha")

    assert created == [
        {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "device": None,
        }
    ]
    assert model.calls[0][0] == ["doc:alpha", "doc:beta"]
    assert model.calls[0][1]["batch_size"] == 7
    assert model.calls[0][1]["show_progress_bar"] is True
    assert model.calls[1][0] == ["query:alpha"]
    assert documents.shape == (2, 2)
    assert query.tolist() == [3.0, 4.0]
    assert embedder.similarity("alpha", "beta") == pytest.approx(0.8)


def test_hf_embedder_handles_empty_input_and_zero_vectors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = FakeSentenceModel()
    install_fake_sentence_transformer(monkeypatch, model)
    embedder = HFEmbedder(query_prefix="query:", doc_prefix="doc:")

    assert embedder.embedding_documents([]).shape == (0, 2)
    assert model.calls == []
    assert embedder.similarity("zero", "alpha") == 0.0


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"model_name": " "}, "model_name"),
        ({"device": True}, "device"),
        ({"batch_size": 0}, "batch_size"),
        ({"normalize": "yes"}, "normalize"),
    ],
)
def test_hf_embedder_rejects_invalid_configuration(
    monkeypatch: pytest.MonkeyPatch,
    kwargs: dict[str, object],
    message: str,
) -> None:
    install_fake_sentence_transformer(monkeypatch, FakeSentenceModel())

    with pytest.raises(ValueError, match=message):
        HFEmbedder(**kwargs)


def test_hf_embedder_rejects_bad_model_output(monkeypatch: pytest.MonkeyPatch) -> None:
    model = FakeSentenceModel()
    model.vectors["doc:alpha"] = [float("nan"), 0.0]
    install_fake_sentence_transformer(monkeypatch, model)
    embedder = HFEmbedder(doc_prefix="doc:")

    with pytest.raises(ValueError, match="non-finite"):
        embedder.embedding_documents(["alpha"])


def test_embedding_index_ranks_by_cosine_and_applies_optional_threshold() -> None:
    index = EmbeddingIndex(FakeEmbedder())
    index.add(
        [
            {"text": "cats", "source": "one"},
            {"text": "diagonal", "source": "two"},
            {"text": "dogs", "source": "three"},
            {"text": "   ", "source": "blank"},
        ],
        show_progress=False,
    )

    matches = index.search("cats", k=3)
    thresholded = index.search("cats", k=3, min_score=0.5)

    assert len(index) == 3
    assert [match["text"] for match in matches] == ["cats", "diagonal", "dogs"]
    assert [match["text"] for match in thresholded] == ["cats", "diagonal"]
    assert matches[0]["score"] == pytest.approx(1.0)
    assert matches[1]["score"] == pytest.approx(0.8)


def test_embedding_index_save_load_and_legacy_loader(
    tmp_path: Path,
) -> None:
    embedder = FakeEmbedder()
    index = EmbeddingIndex(embedder)
    index.add([{"text": "cats", "source": "one"}])
    index.save(tmp_path)

    loaded = EmbeddingIndex.load(tmp_path, embedder)
    legacy_loaded = index.loader(tmp_path, embedder)

    assert len(loaded) == 1
    assert loaded.search("cats") == index.search("cats")
    assert legacy_loaded.search("cats") == index.search("cats")
    assert json.loads((tmp_path / "items.json").read_text(encoding="utf-8")) == index.items


def test_embedding_index_validates_updates_and_empty_round_trip(tmp_path: Path) -> None:
    embedder = FakeEmbedder()
    index = EmbeddingIndex(embedder)
    embedder.bad_output = True

    with pytest.raises(ValueError, match="non-finite"):
        index.add([{"text": "cats"}])
    assert len(index) == 0

    embedder.bad_output = False
    index.save(tmp_path)
    loaded = EmbeddingIndex.load(tmp_path, embedder)
    assert len(loaded) == 0
    assert loaded.search("cats") == []


def test_embedding_index_rejects_invalid_search_arguments() -> None:
    index = EmbeddingIndex(FakeEmbedder())
    with pytest.raises(ValueError, match="Query"):
        index.search(" ")
    with pytest.raises(ValueError, match="k"):
        index.search("cats", k=0)
    with pytest.raises(ValueError, match="min_score"):
        index.search("cats", min_score=float("inf"))


def test_async_embedding_adapter_connects_hf_model_to_rag_retriever(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def exercise() -> None:
        model = FakeSentenceModel()
        install_fake_sentence_transformer(monkeypatch, model)
        embedder = HFEmbedder(query_prefix="query:", doc_prefix="doc:")
        retriever = MemoryVectorRetriever(AsyncEmbeddingAdapter(embedder))

        await retriever.add_documents(
            [
                Document(id="alpha", content="alpha"),
                Document(id="beta", content="beta"),
            ]
        )
        results = await retriever.retrieve("alpha", top_k=2)

        assert [result.document.id for result in results] == ["alpha", "beta"]
        assert results[0].score == pytest.approx(1.0)

    asyncio.run(exercise())
