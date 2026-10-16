class QueryRewriting: 
    def __init__(self, model, style:str | None = "search"): 
        self.model = model
        self.style = style

    def _prompt(self,query):
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

    def improve(self,query): 
        query = query.strip()
        if not query: 
            return query
        result = self.model.think(self._prompt(query=query)).strip()
        return result.strip('"')

    def variants(self,query,n:int|None = 3):
        """Return n different rewrites of the query (useful for RAG / search)."""
        prompt = (
            f"Write {n} different improved versions of this search query, "
            "each using different wording. One per line, no numbering, no extra text.\n\n"
            f"Query: {query}"
        )
        lines = self.model.think(prompt).splitlines()
        return [line.strip("-•* \t") for line in lines if line.strip()][:n]

    

    
    
