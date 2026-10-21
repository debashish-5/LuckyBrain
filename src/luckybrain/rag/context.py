"""Citation-aware context assembly for retrieved documents."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from luckybrain.core.models import RetrievalResult


@dataclass(frozen=True, slots=True)
class CitationSource:
    """A source reference corresponding to one labeled context section."""

    label: str
    document_id: str
    score: float
    metadata: Mapping[str, object]
    truncated: bool = False


@dataclass(frozen=True, slots=True)
class ContextAssembly:
    """Prompt-ready context and the source references used to assemble it."""

    context: str
    sources: tuple[CitationSource, ...]


@dataclass(frozen=True, slots=True)
class CitationContextBuilder:
    """Format retrieval results as labeled context with a source map.

    An optional character limit bounds the assembled text. If the limit is
    reached partway through a source, that source is marked as truncated and
    lower-ranked sources are omitted. Character limits are not token limits.
    """

    max_characters: int | None = None

    def __post_init__(self) -> None:
        if self.max_characters is not None and (
            isinstance(self.max_characters, bool)
            or not isinstance(self.max_characters, int)
            or self.max_characters < 1
        ):
            raise ValueError("max_characters must be a positive integer or None.")

    def assemble(self, results: Sequence[RetrievalResult]) -> ContextAssembly:
        """Build labeled context and deduplicated source references in result order."""
        sections: list[str] = []
        sources: list[CitationSource] = []
        seen_ids: set[str] = set()
        used_characters = 0

        for result in results:
            document = result.document
            if document.id in seen_ids:
                continue

            label = f"S{len(sources) + 1}"
            prefix = f"[{label}]\n"
            separator = "\n\n" if sections else ""
            available = (
                None
                if self.max_characters is None
                else self.max_characters - used_characters - len(separator) - len(prefix)
            )
            if available is not None and available < 1:
                break

            content = document.content if available is None else document.content[:available]
            truncated = len(content) < len(document.content)
            if not content:
                break

            sections.append(f"{prefix}{content}")
            sources.append(
                CitationSource(
                    label=label,
                    document_id=document.id,
                    score=result.score,
                    metadata=dict(document.metadata),
                    truncated=truncated,
                )
            )
            seen_ids.add(document.id)
            used_characters += len(separator) + len(prefix) + len(content)
            if truncated:
                break

        return ContextAssembly(context="\n\n".join(sections), sources=tuple(sources))
