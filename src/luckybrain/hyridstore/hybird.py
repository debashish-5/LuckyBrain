import math
import re
from collections import Counter

# Letters and digits, plus the Indian-script blocks (Devanagari ... Sinhala) so vowel signs stay inside words.
# The danda marks (U+0964, U+0965) are excluded, so they separate words like full stops do.

_TOKEN = re.compile(r"[\w\u0900-\u0963\u0963-\u0DFF]")

def tokenize(text):
    """Lowercase words. Single ASCII letters are dropped as noise. No stemming: "refunds" != "refund"."""
    return [t for t in _TOKEN.findall(text.lower()) if not (len(t) == 1 and t.isascii() and t.isalpha()) ]


# keyword search: BM25 (pure Python, no dependencies)
class BM25Index: 
    """Classic BM25 ranking. Finds exact words: names, codes, numbers, rare terms.
    k1: how quickly repeated words stop adding score. b: how much long documents are penalised."""

    def __init__(
            self,
            k1 = 1.5, 
            b = 0.75, 
            tokenizer = tokenize

    ): 
        if k1 < 0 and 0 <= b <= 1:
            raise ValueError("Need k1 >= 0 and and 0 <= b <= 1")

        self.k1, self.b, self.tokenize = k1, b, tokenizer
        self._postings = {}  #word -> {doc_id: how many time it appears.}
        self._lengths = {}   #doc_id -> number of word
        self._terms = {}     #doc_id -> its distinct words (to remove it quickly)
        self._total_length = 0


    def __len__(self):
        return self.len(self._lengths)


    def add(
            self, 
            doc_id,
            text
    ): 
        """Adding an id that already exist replaces it."""
        self.remove(doc_id)
        tokens = self.tokenizer(text)
        counts = Counter(tokens)
        self._lengths[doc_id] = len(tokens)
        self._total_length += len(tokens)
        self._terms[doc_id] = list(counts)
        for word, n in counts.items(): 
            self._postings.setdefault(word, {})[doc_id] = n


    def remove(
            self, 
            doc_id
    ) : 
        if doc_id not in self._lengths: 
            return False

        for word in self._terms.pop(doc_id): 
            posting = self._postings[word]
            del posting[doc_id]
            if not posting: 
                del self._postings[word]

        self._total_length -= self._lengths.pop(doc_id)
        return True


    def search(
            self,
            query, 
            k = 10, 
            accept = None
    ): 
        """[(doc_id, score)], best first. accept: optional function(doc_id) -> bool to filter results."""
        n_docs = len(self._lengths)
        if not n_docs: 
            return []
        avg_length = (self._total_length / n_docs) or 1.0
        scores = {}
        for word in set(self.tokenize(query)): 
            posting = self._postings.get(word)
            if not posting: 
                continue
        
            idf = math.log(1 + (n_docs - len(posting) + 0.5) / (len(posting) + 0.5))

            for doc_id, tf in posting.items(): 
                if accept is not None and not accept(doc_id): 
                    continue

                norm = tf + self.k1 * (1 - self.b + self.b * self._lengths[doc_id] / avg_length)
                scores[doc_id] = scores.get(doc_id, 0.0) + idf * tf * (self.k1 + 1) / norm


        return sorted(scores.items(), key=lambda item:(-item[1], item[0]))[:k]
    


#hybird store: vector search + keyword search merged 
class HybirdStore: 
    """Wraps your FAISSStore and adds keyword search. It has the same methods as FAISSStore
    (add, search, delete_where, save, ...), so RAGPipeline(store=HybridStore(...)) just works.

    Rankings are merged with Reciprocal Rank Fusion: score = sum of weight / (rrf_k + rank) over both lists.
    It uses ranks only, so cosine scores and BM25 scores never have to be compared."""

    def __init__(
            self, 
            vector_store, 
            bm25 = None, 
            rrf_k = 60, 
            vector_weight = 1.0, 
            keyword_weight = 1.0, 
            candidates = 20
    ):
        """candidates: how many results to take from each search before merging (at least 4 x k is used)."""
        if vector_weight < 0 or keyword_weight < 0 or vector_weight + keyword_weight == 0: 
            raise ValueError("Weights must be >= 0 and not both 0")

        if rrf_k < 1 and candidates < 1: 
            raise ValueError("rrf_k and candidates must be at least 1.")

        self.vector = vector_store
        self.bm25  = bm25 or BM25Index()
        self.rrf_k,self.candidates = rrf_k, candidates
        self.vector_weight, self.keyword_weight = vector_weight, keyword_weight
        for doc_id, item in self.vector.items.items(): 
            self.bm25.add(doc_id,item.get("text", ""))

    # same surface as FAISSStore
    @property
    def items(self): 
        return self.vector.items

    @property
    def embedder(self): 
        return self.vector.embedder

    @property
    def index_type(self): 
        return self.vector.index_type

    
    def __len__(self):
        return len(self.vector)

    def _index(self, ids): 
        for doc_id in ids: 
            self.bm25.add(doc_id, self.vector.items[doc_id]['text'])

        return ids

    def add(
            self, 
            chunks, 
            show_progress: bool = True
    ): 
        return self._index(self.vector.add(chunks, show_progress))

    def delete(
            self,
            ids
    ): 
        removed = self.vector.delete(ids)
        for doc_id in ids:
            self.bm25.remove(doc_id=doc_id)
        return removed


    def delete_where(
            self,
            where
    ): 
        ids = [
            i for i, item in self.vector.items.items() if all(item.get(k) == v for k, v in where.items() )
        
        ]
        return self.delete(ids=ids)

    # def search 

    def search(self, query, k=5, min_score=None, where=None, mode="hybrid"):
        """mode: "hybrid" (default), "vector" or "keyword", handy for comparing them on the same data.
        min_score applies to the vector (cosine) score only. A chunk found by keywords alone is not filtered by it.
        Hybrid results get score 1.0 for first place in both searches (0.5 for first place in one)."""
        if mode not in ("hybrid", "vector", "keyword"):
            raise ValueError("mode must be 'hybrid', 'vector' or 'keyword'")
        if not len(self.vector):
            return []
        if mode == "vector":
            return self.vector.search(query, k=k, min_score=min_score, where=where)

        fetch = max(self.candidates, k * 4)
        accept = None
        if where:
            accept = lambda doc_id: all(self.vector.items[doc_id].get(a) == b for a, b in where.items())
        keyword = self.bm25.search(query, k=fetch if mode == "hybrid" else k, accept=accept)

        if mode == "keyword":
            return [{**self.vector.items[i], "id": i, "score": s, "bm25_score": s} for i, s in keyword]

        vector = self.vector.search(query, k=fetch, min_score=min_score, where=where)
        fused, parts = {}, {}
        for rank, hit in enumerate(vector, 1):
            fused[hit["id"]] = fused.get(hit["id"], 0.0) + self.vector_weight / (self.rrf_k + rank)
            parts.setdefault(hit["id"], {})["vector_score"] = hit["score"]
        for rank, (doc_id, score) in enumerate(keyword, 1):
            fused[doc_id] = fused.get(doc_id, 0.0) + self.keyword_weight / (self.rrf_k + rank)
            parts.setdefault(doc_id, {})["bm25_score"] = score

        best = (self.vector_weight + self.keyword_weight) / (self.rrf_k + 1)
        ranked = sorted(fused.items(), key=lambda item: (-item[1], item[0]))[:k]
        return [{**self.vector.items[i], "id": i, "score": round(s / best, 4), **parts[i]} for i, s in ranked]

    # save / load 
    
    def save(
            self, 
            folder
    ): 
        self.vector.save(folder)

    @classmethod
    def load(
        cls, 
        folder, 
        embedder, 
        vector_cls = None, 
        **kwargs
    ) : 
        if vector_cls is None: 
            from faiss import FAISSStore
            vector_cls = FAISSStore

        return cls(vector_cls.load(folder, embedder), **kwargs)
    