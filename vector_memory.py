"""
Bruce AI — Vector Memory (Real Semantic Search)

Uses ChromaDB for actual vector embeddings and semantic search.
Falls back to keyword matching if ChromaDB is not available.

This replaces the simple JSONL keyword matching with REAL memory.
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("Bruce.VectorMemory")

MEMORY_DIR = Path("./data/vector_memory")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

# Try to import ChromaDB
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.info("ChromaDB not installed. Using keyword fallback. Install: pip install chromadb")


class VectorMemory:
    """Real vector memory with semantic search."""

    def __init__(self, collection_name: str = "bruce_memory"):
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._fallback_store: List[dict] = []

        if CHROMA_AVAILABLE:
            try:
                self._client = chromadb.PersistentClient(
                    path=str(MEMORY_DIR / "chromadb")
                )
                self._collection = self._client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
                count = self._collection.count()
                logger.info(f"VectorMemory: ChromaDB loaded with {count} entries")
            except Exception as e:
                logger.error(f"ChromaDB init failed: {e}. Using fallback.")
                self._client = None
        else:
            # Load fallback store
            fallback_path = MEMORY_DIR / "fallback_store.json"
            if fallback_path.exists():
                try:
                    self._fallback_store = json.loads(fallback_path.read_text(encoding="utf-8"))
                except Exception:
                    self._fallback_store = []

    @property
    def is_vector(self) -> bool:
        """True if using real vector search (ChromaDB)."""
        return self._collection is not None

    def store(self, content: str, metadata: dict = None, doc_id: str = None) -> str:
        """Store a memory with vector embedding."""
        if not doc_id:
            doc_id = hashlib.md5(content.encode()).hexdigest()[:12]

        meta = metadata or {}
        meta["stored_at"] = datetime.now(timezone.utc).isoformat()
        # ChromaDB doesn't support nested dicts in metadata
        flat_meta = {k: str(v) if not isinstance(v, (str, int, float, bool)) else v
                     for k, v in meta.items()}

        if self._collection is not None:
            try:
                self._collection.upsert(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[flat_meta],
                )
                return doc_id
            except Exception as e:
                logger.error(f"ChromaDB store failed: {e}")

        # Fallback
        self._fallback_store.append({
            "id": doc_id,
            "content": content,
            "metadata": meta,
        })
        self._save_fallback()
        return doc_id

    def search(self, query: str, limit: int = 5, where: dict = None) -> List[dict]:
        """Semantic search across memories."""
        if self._collection is not None:
            try:
                kwargs = {
                    "query_texts": [query],
                    "n_results": limit,
                }
                if where:
                    kwargs["where"] = where
                results = self._collection.query(**kwargs)

                if not results["ids"][0]:
                    return []

                return [
                    {
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 0,
                        "relevance": 1 - (results["distances"][0][i] if results.get("distances") else 0),
                    }
                    for i in range(len(results["ids"][0]))
                ]
            except Exception as e:
                logger.error(f"ChromaDB search failed: {e}")

        # Fallback: keyword matching
        query_words = set(query.lower().split())
        scored = []
        for entry in self._fallback_store:
            content_words = set(entry["content"].lower().split())
            overlap = len(query_words & content_words)
            if overlap > 0:
                scored.append((overlap / max(len(query_words), 1), entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"id": e["id"], "content": e["content"], "metadata": e["metadata"],
             "relevance": score}
            for score, e in scored[:limit]
        ]

    def store_conversation(self, user_msg: str, bruce_msg: str, user_id: str = "federico"):
        """Store a conversation turn as memory."""
        self.store(
            f"User: {user_msg}\nBruce: {bruce_msg}",
            metadata={
                "type": "conversation",
                "user_id": user_id,
                "user_message": user_msg[:200],
            },
        )

    def store_fact(self, fact: str, domain: str, source: str = "learned"):
        """Store a fact for later retrieval."""
        self.store(fact, metadata={"type": "fact", "domain": domain, "source": source})

    def store_decision(self, decision: str, context: str, outcome: str = None):
        """Store a decision for learning from past actions."""
        self.store(
            f"Decision: {decision}\nContext: {context}\nOutcome: {outcome or 'pending'}",
            metadata={"type": "decision", "outcome": outcome or "pending"},
        )

    def recall_relevant(self, query: str, limit: int = 5) -> str:
        """Get relevant memories formatted as context string."""
        results = self.search(query, limit=limit)
        if not results:
            return ""
        lines = ["[Relevant memories:]"]
        for r in results:
            relevance = r.get("relevance", 0)
            if relevance > 0.3 or not self.is_vector:  # Lower threshold for keyword
                lines.append(f"  [{relevance:.0%}] {r['content'][:200]}")
        return "\n".join(lines) if len(lines) > 1 else ""

    def get_stats(self) -> dict:
        """Memory statistics."""
        if self._collection is not None:
            count = self._collection.count()
            return {
                "backend": "ChromaDB (vector)",
                "entries": count,
                "collection": self.collection_name,
                "semantic_search": True,
            }
        return {
            "backend": "Keyword (fallback)",
            "entries": len(self._fallback_store),
            "semantic_search": False,
        }

    def _save_fallback(self):
        fallback_path = MEMORY_DIR / "fallback_store.json"
        fallback_path.write_text(
            json.dumps(self._fallback_store[-5000:], indent=2, default=str),
            encoding="utf-8",
        )


# Singleton
_memory = None

def get_vector_memory() -> VectorMemory:
    global _memory
    if _memory is None:
        _memory = VectorMemory()
    return _memory
