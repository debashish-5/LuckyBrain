"""Provider-neutral domain models shared across components."""

from dataclasses import dataclass, field
from collections.abc import Mapping


@dataclass(frozen=True, slots=True)
class Document:
    """A source document or passage with stable identity and metadata."""

    id: str
    content: str
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Document id must not be empty.")
        if not self.content.strip():
            raise ValueError("Document content must not be empty.")


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """A document returned by retrieval with its provider-defined relevance score."""

    document: Document
    score: float