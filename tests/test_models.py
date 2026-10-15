import pytest

from luckybrain import Document, RetrievalResult


def test_document_keeps_metadata_and_has_independent_defaults() -> None:
    first = Document(id="doc-1", content="Text", metadata={"source": "guide"})
    second = Document(id="doc-2", content="Other text")

    assert first.metadata == {"source": "guide"}
    assert second.metadata == {}
    assert first.metadata is not second.metadata


@pytest.mark.parametrize(
    ("document_id", "content"),
    [("", "Text"), ("   ", "Text"), ("doc-1", ""), ("doc-1", "  ")],
)
def test_document_rejects_empty_identity_or_content(document_id: str, content: str) -> None:
    with pytest.raises(ValueError):
        Document(id=document_id, content=content)


def test_retrieval_result_keeps_document_and_score() -> None:
    document = Document(id="doc-1", content="Text")

    result = RetrievalResult(document=document, score=0.92)

    assert result.document is document
    assert result.score == 0.92
