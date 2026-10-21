"""Deterministic text chunking for retrieval workflows."""

from dataclasses import dataclass

from luckybrain.core.models import Document


@dataclass(frozen=True, slots=True)
class DocumentChunker:
    """Split a document into overlapping, source-linked character chunks.

    Chunks prefer paragraph, sentence, and word boundaries when one is
    available in the latter half of a chunk. Character offsets refer to the
    original document content; this is a character-based splitter, not a
    tokenizer.
    """

    chunk_size: int = 1000
    chunk_overlap: int = 200

    def __post_init__(self) -> None:
        if (
            isinstance(self.chunk_size, bool)
            or not isinstance(self.chunk_size, int)
            or self.chunk_size < 1
        ):
            raise ValueError("chunk_size must be a positive integer.")
        if (
            isinstance(self.chunk_overlap, bool)
            or not isinstance(self.chunk_overlap, int)
            or not 0 <= self.chunk_overlap < self.chunk_size
        ):
            raise ValueError("chunk_overlap must be an integer from 0 to chunk_size - 1.")

    def split(self, document: Document) -> list[Document]:
        """Return chunks with deterministic IDs and source offsets in metadata."""
        content = document.content
        chunks: list[Document] = []
        start = 0

        while start < len(content):
            end = min(start + self.chunk_size, len(content))
            if end < len(content):
                boundary_start = start + self.chunk_size // 2
                boundaries = (
                    content.rfind("\n\n", boundary_start, end),
                    content.rfind(". ", boundary_start, end),
                    content.rfind("\n", boundary_start, end),
                    content.rfind(" ", boundary_start, end),
                )
                boundary = max(boundaries)
                if boundary >= boundary_start:
                    boundary_text = content[boundary : boundary + 2]
                    end = boundary + (2 if boundary_text in {"\n\n", ". "} else 1)

            raw_chunk = content[start:end]
            chunk = raw_chunk.strip()
            if chunk:
                leading_whitespace = len(raw_chunk) - len(raw_chunk.lstrip())
                chunk_start = start + leading_whitespace
                chunk_end = chunk_start + len(chunk)
                metadata = {
                    **document.metadata,
                    "source_document_id": document.id,
                    "chunk_index": len(chunks),
                    "char_start": chunk_start,
                    "char_end": chunk_end,
                }
                chunks.append(
                    Document(
                        id=f"{document.id}#chunk-{len(chunks)}",
                        content=chunk,
                        metadata=metadata,
                    )
                )

            if end >= len(content):
                break
            start = max(end - self.chunk_overlap, start + 1)

        return chunks
