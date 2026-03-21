"""
Bruce AI - RAG (Retrieval Augmented Generation) Engine

Complete RAG pipeline that integrates with the existing VectorMemory (ChromaDB)
and KnowledgeIngestor systems. Uses Ollama embeddings when available, falls back
to TF-IDF for lightweight operation without an LLM server.

Pipeline: embed query -> retrieve relevant chunks -> augment prompt -> return
"""

import hashlib
import logging
import math
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests as http_requests

logger = logging.getLogger("Bruce.RAGEngine")

# ---------------------------------------------------------------------------
# Paths (aligned with existing vector_memory.py)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = BASE_DIR / "data" / "vector_memory" / "chromadb"

# ---------------------------------------------------------------------------
# Optional imports
# ---------------------------------------------------------------------------
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.info("ChromaDB not installed - RAG will use in-memory TF-IDF fallback")

# ---------------------------------------------------------------------------
# Ollama embedding helpers
# ---------------------------------------------------------------------------
OLLAMA_BASE = "http://localhost:11434"
OLLAMA_EMBED_MODELS = ["nomic-embed-text", "mxbai-embed-large"]

_ollama_embed_model: Optional[str] = None
_ollama_checked = False


def _detect_ollama_embed_model() -> Optional[str]:
    """Detect which Ollama embedding model is available."""
    global _ollama_embed_model, _ollama_checked
    if _ollama_checked:
        return _ollama_embed_model
    _ollama_checked = True

    try:
        resp = http_requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
        if resp.status_code != 200:
            return None
        models = [m.get("name", "") for m in resp.json().get("models", [])]
        for candidate in OLLAMA_EMBED_MODELS:
            for m in models:
                if candidate in m:
                    _ollama_embed_model = candidate
                    logger.info("Ollama embed model detected: %s", candidate)
                    return _ollama_embed_model
    except Exception as e:
        logger.debug("Ollama not reachable for embeddings: %s", e)
    return None


def embed_text(text: str) -> Optional[List[float]]:
    """Get embeddings from Ollama. Returns None if unavailable."""
    model = _detect_ollama_embed_model()
    if model is None:
        return None
    try:
        resp = http_requests.post(
            f"{OLLAMA_BASE}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get("embedding")
    except Exception as e:
        logger.debug("Ollama embedding failed: %s", e)
    return None


# ---------------------------------------------------------------------------
# TF-IDF fallback embeddings
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """Simple word tokenizer."""
    return re.findall(r"[a-zA-Z0-9]{2,}", text.lower())


class TFIDFEmbedder:
    """Lightweight TF-IDF embedder used when Ollama is not available."""

    def __init__(self):
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_count = 0

    def fit_partial(self, text: str):
        """Incrementally update IDF stats with a new document."""
        tokens = set(_tokenize(text))
        self.doc_count += 1
        for tok in tokens:
            if tok not in self.vocab:
                self.vocab[tok] = len(self.vocab)
            self.idf[tok] = self.idf.get(tok, 0) + 1

    def embed(self, text: str, dim: int = 384) -> List[float]:
        """Produce a fixed-size pseudo-embedding via hashed TF-IDF."""
        tokens = _tokenize(text)
        if not tokens:
            return [0.0] * dim

        tf = Counter(tokens)
        total = len(tokens)

        vec = [0.0] * dim
        for tok, count in tf.items():
            tf_val = count / total
            idf_val = math.log((self.doc_count + 1) / (self.idf.get(tok, 0) + 1)) + 1
            score = tf_val * idf_val
            # Hash-project into fixed dimension
            idx = hash(tok) % dim
            vec[idx] += score

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


# Module-level TF-IDF instance
_tfidf = TFIDFEmbedder()


def embed_text_fallback(text: str) -> List[float]:
    """TF-IDF fallback embedding (always available)."""
    return _tfidf.embed(text)


# ---------------------------------------------------------------------------
# RAG Engine
# ---------------------------------------------------------------------------

class RAGEngine:
    """
    Full RAG pipeline that ties together:
      - Ollama or TF-IDF embeddings
      - ChromaDB vector store (shared with VectorMemory)
      - KnowledgeIngestor chunking logic
      - Prompt augmentation for LLM queries
    """

    RAG_COLLECTION = "bruce_rag"

    def __init__(
        self,
        collection_name: str = None,
        chroma_path: str = None,
    ):
        self.collection_name = collection_name or self.RAG_COLLECTION
        self._chroma_path = chroma_path or str(CHROMA_DIR)
        self._client = None
        self._collection = None
        self._use_ollama = False
        self._init_store()

    # ----- initialisation ------------------------------------------------

    def _init_store(self):
        if CHROMA_AVAILABLE:
            try:
                self._client = chromadb.PersistentClient(path=self._chroma_path)
                # When Ollama embeddings are available we store them ourselves;
                # otherwise let ChromaDB use its default embedder.
                self._use_ollama = _detect_ollama_embed_model() is not None
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info(
                    "RAGEngine: ChromaDB ready (%d docs, ollama_embed=%s)",
                    self._collection.count(),
                    self._use_ollama,
                )
            except Exception as e:
                logger.error("RAGEngine ChromaDB init failed: %s", e)

    # ----- chunking (reuses KnowledgeIngestor logic) ---------------------

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
        """Chunk text with overlap using intelligent boundaries."""
        try:
            from knowledge_ingestor import KnowledgeIngestor
            return KnowledgeIngestor.chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        except ImportError:
            pass
        # Inline fallback
        if not text or not text.strip():
            return []
        text = text.strip()
        if len(text) <= chunk_size:
            return [{"text": text, "index": 0, "char_start": 0, "char_end": len(text)}]
        chunks, pos, idx = [], 0, 0
        while pos < len(text):
            end = min(pos + chunk_size, len(text))
            if end < len(text):
                seg = text[pos:end]
                brk = seg.rfind("\n\n")
                if brk > chunk_size * 0.3:
                    end = pos + brk + 2
                else:
                    sbrk = max(seg.rfind(". "), seg.rfind(".\n"), seg.rfind("? "), seg.rfind("! "))
                    if sbrk > chunk_size * 0.3:
                        end = pos + sbrk + 2
                    else:
                        wbrk = seg.rfind(" ")
                        if wbrk > chunk_size * 0.5:
                            end = pos + wbrk + 1
            ct = text[pos:end].strip()
            if ct:
                chunks.append({"text": ct, "index": idx, "char_start": pos, "char_end": end})
                idx += 1
            pos = max(end - overlap, pos + 1)
            if pos >= len(text):
                break
        return chunks

    # ----- index_document ------------------------------------------------

    def index_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> Dict[str, Any]:
        """Chunk a document, embed each chunk, and store in ChromaDB."""
        if not text or not text.strip():
            return {"status": "empty", "chunks_indexed": 0}

        chunks = self._chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        meta = metadata or {}
        source = meta.get("source", "unknown")
        indexed = 0

        for chunk in chunks:
            chunk_text = chunk["text"]
            doc_id = hashlib.md5(
                f"{source}:{chunk['index']}:{chunk_text[:80]}".encode()
            ).hexdigest()[:16]

            flat_meta = {
                "source": str(source),
                "chunk_index": chunk["index"],
                "char_start": chunk["char_start"],
                "char_end": chunk["char_end"],
                "indexed_at": datetime.now(timezone.utc).isoformat(),
            }
            for k, v in meta.items():
                if k not in flat_meta:
                    flat_meta[k] = str(v) if not isinstance(v, (str, int, float, bool)) else v

            # Update TF-IDF stats regardless (for fallback)
            _tfidf.fit_partial(chunk_text)

            if self._collection is not None:
                try:
                    kwargs: Dict[str, Any] = {
                        "ids": [doc_id],
                        "documents": [chunk_text],
                        "metadatas": [flat_meta],
                    }
                    # If Ollama embeddings available, supply them explicitly
                    if self._use_ollama:
                        emb = embed_text(chunk_text)
                        if emb is not None:
                            kwargs["embeddings"] = [emb]
                    self._collection.upsert(**kwargs)
                    indexed += 1
                except Exception as e:
                    logger.warning("RAG index chunk failed: %s", e)
            else:
                indexed += 1  # counted even without chroma for stats

        logger.info("RAGEngine indexed %d/%d chunks from '%s'", indexed, len(chunks), source)
        return {
            "status": "indexed",
            "chunks_indexed": indexed,
            "total_chunks": len(chunks),
            "source": source,
        }

    # ----- query (retrieve) ----------------------------------------------

    def query(self, question: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve the top_k most relevant chunks for a question."""
        if self._collection is None or self._collection.count() == 0:
            return self._fallback_keyword_search(question, top_k)

        try:
            kwargs: Dict[str, Any] = {"n_results": min(top_k, self._collection.count())}

            if self._use_ollama:
                emb = embed_text(question)
                if emb is not None:
                    kwargs["query_embeddings"] = [emb]
                else:
                    kwargs["query_texts"] = [question]
            else:
                kwargs["query_texts"] = [question]

            results = self._collection.query(**kwargs)

            if not results["ids"][0]:
                return []

            output = []
            for i in range(len(results["ids"][0])):
                output.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else 0,
                    "relevance": round(
                        1 - (results["distances"][0][i] if results.get("distances") else 0), 4
                    ),
                })
            return output

        except Exception as e:
            logger.warning("RAG query failed, falling back to keyword: %s", e)
            return self._fallback_keyword_search(question, top_k)

    def _fallback_keyword_search(self, question: str, top_k: int) -> List[Dict[str, Any]]:
        """Keyword search fallback when ChromaDB query fails."""
        try:
            from knowledge_ingestor import KnowledgeIngestor
            ki = KnowledgeIngestor()
            results = ki.search(question, limit=top_k)
            return [
                {
                    "id": r.get("source_id", ""),
                    "text": r.get("text", ""),
                    "metadata": r.get("metadata", {}),
                    "relevance": r.get("_relevance", 0),
                }
                for r in results
            ]
        except Exception:
            pass
        return []

    # ----- augment_prompt ------------------------------------------------

    @staticmethod
    def augment_prompt(
        question: str,
        context_chunks: List[Dict[str, Any]],
        max_context_chars: int = 3000,
    ) -> str:
        """Build an augmented prompt with retrieved context."""
        if not context_chunks:
            return question

        context_parts = []
        total_chars = 0
        for chunk in context_chunks:
            text = chunk.get("text", "")
            relevance = chunk.get("relevance", 0)
            source = chunk.get("metadata", {}).get("source", "memory")
            if total_chars + len(text) > max_context_chars:
                remaining = max_context_chars - total_chars
                if remaining > 50:
                    text = text[:remaining] + "..."
                else:
                    break
            context_parts.append(f"[{relevance:.0%} | {source}] {text}")
            total_chars += len(text)

        context_block = "\n---\n".join(context_parts)

        return (
            f"Use the following context to answer the question. "
            f"If the context is not relevant, answer from your general knowledge.\n\n"
            f"=== CONTEXT ===\n{context_block}\n=== END CONTEXT ===\n\n"
            f"Question: {question}"
        )

    # ----- rag_query (full pipeline) -------------------------------------

    def rag_query(
        self,
        question: str,
        top_k: int = 5,
        max_context_chars: int = 3000,
    ) -> Dict[str, Any]:
        """
        Full RAG pipeline:
          1. Retrieve relevant chunks for the question
          2. Build an augmented prompt
          3. Return the augmented prompt and retrieved context

        The caller (orchestrator) is responsible for sending the augmented
        prompt to the LLM.
        """
        start = time.perf_counter()

        chunks = self.query(question, top_k=top_k)
        augmented = self.augment_prompt(question, chunks, max_context_chars=max_context_chars)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        return {
            "augmented_prompt": augmented,
            "chunks_retrieved": len(chunks),
            "chunks": chunks,
            "elapsed_ms": elapsed_ms,
            "embedding_backend": "ollama" if self._use_ollama else "default/tfidf",
        }

    # ----- Also integrate with existing VectorMemory ---------------------

    def index_from_vector_memory(self) -> Dict[str, Any]:
        """
        Pull existing entries from the bruce_memory collection (VectorMemory)
        into the RAG collection so RAG queries can leverage conversation history.
        """
        if not CHROMA_AVAILABLE or self._client is None:
            return {"status": "skipped", "reason": "ChromaDB not available"}

        try:
            memory_col = self._client.get_or_create_collection(name="bruce_memory")
            count = memory_col.count()
            if count == 0:
                return {"status": "empty", "reason": "bruce_memory has 0 entries"}

            batch_size = 100
            indexed = 0
            offset = 0
            while offset < count:
                batch = memory_col.get(
                    limit=batch_size,
                    offset=offset,
                    include=["documents", "metadatas"],
                )
                if not batch["ids"]:
                    break
                for i, doc_id in enumerate(batch["ids"]):
                    doc = batch["documents"][i] if batch["documents"] else ""
                    meta = batch["metadatas"][i] if batch["metadatas"] else {}
                    if doc:
                        rag_id = f"vm_{doc_id}"
                        meta_flat = {
                            k: str(v) if not isinstance(v, (str, int, float, bool)) else v
                            for k, v in meta.items()
                        }
                        meta_flat["source"] = "vector_memory"
                        self._collection.upsert(
                            ids=[rag_id],
                            documents=[doc],
                            metadatas=[meta_flat],
                        )
                        indexed += 1
                offset += batch_size

            logger.info("RAGEngine: indexed %d entries from VectorMemory", indexed)
            return {"status": "synced", "entries_indexed": indexed}
        except Exception as e:
            logger.warning("RAGEngine sync from VectorMemory failed: %s", e)
            return {"status": "error", "error": str(e)}

    # ----- stats ---------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        count = 0
        if self._collection is not None:
            try:
                count = self._collection.count()
            except Exception:
                pass
        return {
            "collection": self.collection_name,
            "document_count": count,
            "chroma_available": CHROMA_AVAILABLE,
            "ollama_embeddings": self._use_ollama,
            "ollama_model": _ollama_embed_model,
            "tfidf_vocab_size": len(_tfidf.vocab),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """Get or create the singleton RAGEngine instance."""
    global _engine
    if _engine is None:
        _engine = RAGEngine()
    return _engine
