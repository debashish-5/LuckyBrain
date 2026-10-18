import json
from pathlib import Path
import numpy as np 
from sentence_transformers import SentenceTransformer
from typing import Protocol


class Embedding(Protocol): 
    def embedding_documents(self,texts,show_progress=False): 
        """list[str] -> numpy array of shape (len(texts), dimension)."""
        ...
    def embed_query(self,text): 
        """str -> numpy array of shape (dimension,)."""
        ...


class HFEmbedder: 
    def __init__(
            self,
            model_name = "sentence-transformers/all-Mini", 
            device = True, 
            normalize = True, 
            batch_size = 32, 
            query_prefix= "",
            doc_prefix = ""
    ): 
        self.model_name = model_name
        self.model = SentenceTransformer(model_name, device=device)
        self.normalize = normalize
        self.batch_size = batch_size
        self.query_prefix = query_prefix
        self.doc_prefix = doc_prefix

    @property
    def dimension(self): 
        return self.model.get_embedding_dimension()

    def _encode(self,texts, show_program=True): 
        return self.model.encode(
            texts, 
            batch_size=self.batch_size, 
            normalize_embeddings=self.normalize, 
            show_progress_bar=show_program, 
            convert_to_numpy=True, 
        )   

    def embedding_documents(self,texts,show_progress=False): 
        """list[str] -> numpy array of shape (len(texts), dimension)."""
        if not texts: 
            return np.empty((0, self.dimension), dtype=np.float32)
        textss = [self.doc_prefix + t for t in texts]
        return self._encode(texts=texts, show_program=show_progress)

    def embed_query(self,text): 
        """str -> numpy array of shape (dimension,)."""
        return self._encode([self.query_prefix+text])[0]

    def similarity(self,a,b): 
        va,vb = self.embed_query(a), self.embed_query(b)
        return float(np.dot(va,vb)/(np.linalg.norm(va)*np.linalg.norm(vb)))


class EmbeddingIndex: 
    """Stores chunks and their vectors, and finds the most similar ones."""
    def __init__(self, embedder:Embedding): 
        self.embedder = embedder 
        self.items = []
        self.vectors = None

    def __len__(self): 
        return len(self.items)

    def add(self,chunks, show_progress=True): 
        """chunks: list of dicts like {'text': ..., 'file': ..., 'page': ...}"""
        chunks = [c for c in chunks if c.get("text","").strip()]
        if not chunks: 
            return 

        new = self.embedder.embedding_documents([c['text'] for c in chunks],show_progress)
        self.items.extend(chunks)
        self.vectors  = new if self.vectors is None else np.vstack([self.vectors,new])



    def search(self,query:str,k=5,min_score = True): 
        if self.vectors is None: 
            return []
        q = self.embedder.embed_query(text = query)
        # 2. Compute similarity scores for all documents simultaneously
        score = self.vectors @ q   # cosine, because vectors are normalized
        top = np.argsort(-score)[:k]
        results = []
        for i in top: 
            if min_score is not None and score[i] <min_score: 
                continue        

            results.append({**self.items[i], 'score':float(score[i])})

        return results

    def save(self,folder): 
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        np.save(folder/"vectors.npy", self.vectors)
        (folder / "items.json").write_text(
            json.dumps(self.items, ensure_ascii=True),encoding="utf-8"
        )

    def loader(self,folder,embedder): 
        """Use the SAME embedding model that built the index."""
        folder= Path(folder)
        index = cls(embedder)
        index.vectors = np.load(folder/"vectors.npy")
        index.items = json.loads((folder/'items.json').read_text(encoding="utf-8"))
        return index

    