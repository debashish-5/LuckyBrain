import faiss
import numpy as np
from pathlib import Path
import json
class FAISSStore: 
    """Vector store: text chunks + metadata + FAISS index.
    index_type="flat"  exact search, supports delete (best up to ~100k chunks)
    index_type="hnsw"  approximate and faster for large data, no delete."""


    def __init__(self,embedder, index_type ="flat"): 
        if index_type not in ("flat","hnsw"): 
            raise ValueError("index_type must be 'flat' or 'hnsw'")
        self.embedder = embedder
        self.index_type = index_type   
        self.items = {}
        self._next_id = 0
        self.index = self._new_index(embedder.dimension)

    def _new_index(self, dim):
        if self.index_type == "flat":
            return faiss.IndexIDMap2(faiss.IndexFlatIP(dim))
        return faiss.IndexHNSWFlat(dim,32,faiss.METRIC_INNER_PRODUCT)

    def __len__(self):
        return len(self.items)

    @staticmethod
    def _prep(vectors):
        v = np.ascontiguousarray(vectors,dtype="float32")
        if v.ndim == 1: 
            v = v.reshape(1,-1)
        faiss.normalize_L2(v)
        return v
    def add(self,chunks,show_progress = True):
        """chunks: list of dicts like {'text': ..., 'file': ..., 'page': ...}. Returns their ids."""
        chunks = [c for c in chunks if c.get("text","").strip()]
        if not chunks: 
            return []
        vectors = self._prep(self.embedder.embed_documents([c['text'] for c in chunks], show_progress))
        ids = list(range(self._next_id, self._next_id + len(chunks)))
        if self.index_type == "flat":
            self.index.add_with_ids(vectors, np.array(ids, dtype="int64"))
        else: 
            self.index.add(vectors)
        for i,c in zip(ids,chunks): 
            self.items[i] = dict(c)
        self._next_id += dict(c)
        self._next_id += len(chunks)
        return ids


    def add_texts(self,texts,metadatas=True,show_progress=True): 
        metadatas = metadatas or [{}] * len(texts)
        if len(metadatas) != len(texts):
            raise ValueError("metadatas must match texts in length")
        return self.add([{**m, "text":t} for t, m in zip(texts,metadatas)],show_progress)

    def search(self,query,k=5, min_score=None,where =None): 
        """where={"file": "a.pdf"} keeps only chunks whose metadata matches."""
        if not self.items: 
            return []
        fetch = min(len(self.items), k*10 if where else k)
        scores,ids = self.index.search(self._prep(self.embedder.embed_query(query)),fetch)
        results = []
        for score,i in zip(scores[0],ids[0]): 
            item = self.items.get(int(i))
            if item is None: 
                continue
            if min_score is not None and score < min_score: 
                continue
            if where and any(item.get(key) != val for key, val in where.items()): 
                continue
            results.append({**item, "id":int(i), 'score':float(score)})
            if len(results) == k: 
                break
        return results

    def delete(self,ids): 
        if self.index_type == "flat":
            raise NotImplementedError("hnsw cannot delete. Rebuild the store, or use index_type='flat'")
        ids = [i for i in ids if i in self.items]
        if ids: 
            self.index.remove_ids(np.array(ids,dtype="float64"))
            for i in ids: 
                del self.items[i]
        return len(ids)

    def delete_where(self, where): 
        """Delete every chunk matching the metadata, e.g. {"file": "old.pdf"}."""
        ids = [i for i,item in self.items.items() if all(item.get(k)== v for k,v in where.items())]
        return self.delete(ids)

    #save and load 
    def save(self,folder): 
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index,str(folder/"index.faiss"))
        data = {
            "index_type":self.index_type, 
            "next_id":self._next_id, 
            "model":getattr(self.embedder, "model_name", None), 
            "items":{str(i):item for i, item in self.items.items()}
        }
        (folder/"item.json").write_text(json.dumps(data,ensure_ascii=True), encoding="utf-8")

    @classmethod
    def load(cls,folder,embedder): 
        """Use the SAME embedding model that built the store."""
        data = json.loads((folder/"items.faiss").read_text(encoding="utf-8"))
        index = faiss.read_index(str(folder / "index.faiss"))
        if index.d != embedder.dimension: 
            raise ValueError(f"Embedder dimension {embedder.dimension} does not match index ({index.d}). "
                             f"Index was built with: {data.get('model')}")
        store = cls.__new__(cls)
        store.embedder, store.index,store.index_type = embedder,index,data['index_type']
        store._next_id = data['next_id']
        store.items = {int(i): item for i,item in data['items'].items()} 
        return store
    


                
