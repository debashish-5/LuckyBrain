import pytest

from luckybrain import Document
from luckybrain.rag import DocumentChunker


def test_document_chunker_preserves_source_and_offsets() -> None:
    source = Document(
        id="manual",
        content="First section.  Second section.\n\nThird section.",
        metadata={"path": "manual.txt"},
    )

    chunks = DocumentChunker(chunk_size=24, chunk_overlap=4).split(source)

    assert len(chunks) > 1
    assert [chunk.id for chunk in chunks] == [
        f"manual#chunk-{index}" for index in range(len(chunks))
    ]
    for index, chunk in enumerate(chunks):
        assert chunk.metadata["path"] == "manual.txt"
        assert chunk.metadata["source_document_id"] == "manual"
        assert chunk.metadata["chunk_index"] == index
        start = chunk.metadata["char_start"]
        end = chunk.metadata["char_end"]
        assert isinstance(start, int)
        assert isinstance(end, int)
        assert source.content[start:end] == chunk.content


def test_document_chunker_is_repeatable_and_keeps_short_documents_whole() -> None:
    source = Document(id="brief", content="A short document.")
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=10)

    first = chunker.split(source)
    second = chunker.split(source)

    assert first == second
    assert [chunk.content for chunk in first] == [source.content]


@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap"),
    [(0, 0), (True, 0), (10, -1), (10, 10), (10, True)],
)
def test_document_chunker_rejects_invalid_limits(
    chunk_size: int, chunk_overlap: int
) -> None:
    with pytest.raises(ValueError):
        DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
