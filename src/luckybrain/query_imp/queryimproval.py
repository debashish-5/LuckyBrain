from luckybrain.core.models import ChatModelProtocol


class QueryRewriting:
    """Rewrite search queries using a synchronous chat-model implementation.

    The model must provide ``think(prompt: str) -> str``. This helper delegates
    every rewrite to that model and does not perform retrieval itself.
    """

    def __init__(self, model: ChatModelProtocol, style: str | None = "search") -> None:
        """Create a rewriter.

        Args:
            model: Chat model used to generate rewrites; it must implement
                ``think(prompt: str) -> str``.
            style: Use search-focused wording for ``"search"``. Any other value
                uses question-focused wording.
        """
        self.model = model
        self.style = style

    def _prompt(self, query: str) -> str:
        """Build an instruction prompt for one query."""
        if self.style == "search":
            goal = "a clear, specific search query with the best keywords"
        else:
            goal = "a clear, complete, well-formed question"

        return (
            f"Rewrite the user's query into {goal}.\n"
            "Fix spelling and grammar, remove filler words, and keep the original meaning.\n"
            "Do not add new facts. Reply with ONLY the improved query.\n\n"
            f"Query: {query}"
        )

    def improve(self, query: str) -> str:
        """Return one rewritten query, or an empty string for blank input.

        Args:
            query: User-provided search text.

        Returns:
            The model's rewritten text with surrounding whitespace and quote
            characters removed.
        """
        query = query.strip()
        if not query:
            return query
        result = self.model.think(self._prompt(query=query)).strip()
        return result.strip('"')

    def variants(self, query: str, n: int | None = 3) -> list[str]:
        """Return up to ``n`` alternative query rewrites, one per model line.

        Args:
            query: User-provided search text.
            n: Maximum number of lines to return. ``None`` returns all non-empty
                lines supplied by the model.

        Returns:
            Non-empty model response lines with common list markers removed.
            The result can contain fewer than ``n`` variants when the model
            returns fewer usable lines.
        """
        count = str(n) if n is not None else "several"
        prompt = (
            f"Write {count} different improved versions of this search query, "
            "each using different wording. One per line, no numbering, no extra text.\n\n"
            f"Query: {query}"
        )
        lines = self.model.think(prompt).splitlines()
        return [line.strip("-•* \t") for line in lines if line.strip()][:n]

    def StepBackPrompting(self,query): 
        step_back_prompt = f"""
            ## system 
            You are an expert analyst. Answer the user's question by applying the general background principle or rule provided.
            ## user 
            General Principle Context:\n{query}\n\nOriginal Question: {question}\n\nDetailed Answer:
        """
