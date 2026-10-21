# Text embeddings

LuckyBrain's embedding integrations are optional. Install them separately from
the lightweight package:

```bash
python -m pip install "luckybrain[embeddings]"
```

`HFEmbedder` loads a Sentence Transformers model on the machine where it is
created. The first model use may download weights from Hugging Face; choose
and cache models according to your application's network, privacy, and
licensing requirements. The default is
`sentence-transformers/all-MiniLM-L6-v2`. Set `device` to a Sentence
Transformers device string such as `"cpu"` or `"cuda"`; `None` lets the library
choose. Both document and query prefixes are optional.

## Synchronous use and local index

```python
from luckybrain.embeddings import EmbeddingIndex, HFEmbedder

embedder = HFEmbedder(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    batch_size=32,
    doc_prefix="passage: ",
    query_prefix="query: ",
)
index = EmbeddingIndex(embedder)
index.add(
    [
        {"text": "Cosine similarity compares vector direction.", "source": "notes.md"},
        {"text": "Embeddings map text into numeric vectors.", "source": "guide.md"},
    ]
)
matches = index.search("How are text vectors compared?", k=3, min_score=0.2)
index.save("local-index")

restored = EmbeddingIndex.load("local-index", embedder)
matches = restored.search("How are text vectors compared?")
```

The index retains input records, ranks by cosine similarity even if the model
returns unnormalized vectors, and preserves insertion order for ties. By
default it does not apply a score threshold. Persisted records must be JSON
serializable. The saved vectors do not record the model identity: load an
index only with the same model, prefixes, and vector dimension used to build
it. The index is a simple local file format, not a database or a safe place
for untrusted index files.

## Async RAG retrieval

The model's `encode` calls are synchronous. `AsyncEmbeddingAdapter` runs them
in a worker thread to implement the embedding contract expected by
`MemoryVectorRetriever`:

```python
from luckybrain import Document
from luckybrain.embeddings import AsyncEmbeddingAdapter, HFEmbedder
from luckybrain.rag import DocumentChunker, MemoryVectorRetriever

embedder = HFEmbedder()
retriever = MemoryVectorRetriever(AsyncEmbeddingAdapter(embedder))

async def index_document(document: Document) -> None:
    chunks = DocumentChunker(chunk_size=800, chunk_overlap=100).split(document)
    await retriever.add_documents(chunks)

async def find_sources(query: str):
    return await retriever.retrieve(query, top_k=5)
```

This example uses process-local memory: indexed data is lost when the process
stops. Use a durable vector database integration for persistent or
multi-process workloads. Adding documents with repeated IDs replaces them;
coordinate writes at the application boundary if concurrent updates matter.

See the [RAG and agent contracts](contracts.md) for chunking, provenance, and
retrieval boundaries.
