# knowledge_ingestor.py

"""
Knowledge Ingestor for Bruce AI.
Processes and stores text and web content for the knowledge base,
with intelligent chunking and metadata tracking.
"""

import json
import os
import re
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger("Bruce.KnowledgeIngestor")
logger.setLevel(logging.INFO)

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
KNOWLEDGE_FILE = os.path.join(KNOWLEDGE_DIR, "knowledge_base.jsonl")
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)


class KnowledgeIngestor:
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or KNOWLEDGE_FILE
        self._chunks: List[dict] = []
        self._sources: Dict[str, dict] = {}  # source_id -> metadata
        self._load()

    # ------------------------------------------------------------------ #
    #  Persistence
    # ------------------------------------------------------------------ #

    def _load(self):
        """Load existing knowledge base from disk."""
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        if rec.get("type") == "chunk":
                            self._chunks.append(rec)
                        elif rec.get("type") == "source":
                            self._sources[rec.get("source_id", "")] = rec
                    except json.JSONDecodeError:
                        continue
            logger.info(f"[KnowledgeIngestor] Loaded {len(self._chunks)} chunks from {len(self._sources)} sources")
        except Exception as e:
            logger.warning(f"[KnowledgeIngestor] Could not load: {e}")

    def _persist(self, record: dict):
        """Append a record to the knowledge base file."""
        try:
            with open(self.storage_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"[KnowledgeIngestor] Could not persist: {e}")

    # ------------------------------------------------------------------ #
    #  Text chunking
    # ------------------------------------------------------------------ #

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[dict]:
        """
        Split text into overlapping chunks using intelligent boundaries.
        Tries to split on paragraph breaks, then sentence boundaries, then word boundaries.
        Returns list of chunk dicts with text, index, and character offsets.
        """
        if not text or not text.strip():
            return []

        text = text.strip()

        # If text is small enough, return as single chunk
        if len(text) <= chunk_size:
            return [{
                "text": text,
                "index": 0,
                "char_start": 0,
                "char_end": len(text),
            }]

        chunks = []
        position = 0
        chunk_index = 0

        while position < len(text):
            # Determine the end of this chunk
            end = min(position + chunk_size, len(text))

            if end < len(text):
                # Try to find a good break point
                segment = text[position:end]

                # Try paragraph break first
                para_break = segment.rfind("\n\n")
                if para_break > chunk_size * 0.3:
                    end = position + para_break + 2
                else:
                    # Try sentence break
                    sentence_break = -1
                    for pattern in [". ", ".\n", "! ", "? ", ".\t"]:
                        idx = segment.rfind(pattern)
                        if idx > sentence_break:
                            sentence_break = idx

                    if sentence_break > chunk_size * 0.3:
                        end = position + sentence_break + 2
                    else:
                        # Try word break
                        word_break = segment.rfind(" ")
                        if word_break > chunk_size * 0.5:
                            end = position + word_break + 1

            chunk_text = text[position:end].strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "index": chunk_index,
                    "char_start": position,
                    "char_end": end,
                })
                chunk_index += 1

            # Move position, accounting for overlap
            position = max(end - overlap, position + 1)
            if position >= len(text):
                break

        return chunks

    # ------------------------------------------------------------------ #
    #  Ingestion
    # ------------------------------------------------------------------ #

    def _generate_source_id(self, source: str) -> str:
        """Generate a deterministic source ID."""
        return hashlib.md5(source.encode("utf-8")).hexdigest()[:12]

    def ingest_text(
        self,
        text: str,
        source: str = "manual",
        metadata: Optional[dict] = None,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> dict:
        """
        Process and store text in the knowledge base.
        Text is chunked and each chunk is stored with source metadata.
        """
        if not text or not text.strip():
            return {"status": "empty", "chunks_added": 0}

        source_id = self._generate_source_id(source)

        # Register source
        source_record = {
            "type": "source",
            "source_id": source_id,
            "source": source,
            "metadata": metadata or {},
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "total_chars": len(text),
        }
        self._sources[source_id] = source_record
        self._persist(source_record)

        # Chunk and store
        raw_chunks = self.chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        stored_chunks = []

        for chunk_data in raw_chunks:
            chunk_record = {
                "type": "chunk",
                "source_id": source_id,
                "source": source,
                "text": chunk_data["text"],
                "chunk_index": chunk_data["index"],
                "char_start": chunk_data["char_start"],
                "char_end": chunk_data["char_end"],
                "metadata": metadata or {},
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
            self._chunks.append(chunk_record)
            self._persist(chunk_record)
            stored_chunks.append(chunk_record)

        logger.info(f"[KnowledgeIngestor] Ingested {len(stored_chunks)} chunks from '{source}'")

        return {
            "status": "ingested",
            "source_id": source_id,
            "source": source,
            "chunks_added": len(stored_chunks),
            "total_chars": len(text),
        }

    def ingest_url(self, url: str, metadata: Optional[dict] = None) -> dict:
        """
        Scrape and ingest content from a web URL.
        Attempts to use requests + BeautifulSoup; falls back gracefully.
        """
        try:
            import requests
            from bs4 import BeautifulSoup

            response = requests.get(url, timeout=15, headers={
                "User-Agent": "BruceAI-KnowledgeIngestor/1.0"
            })
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove scripts and styles
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            # Extract text
            text = soup.get_text(separator="\n", strip=True)

            # Clean up excessive whitespace
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = re.sub(r" {2,}", " ", text)

            # Extract title
            title = soup.title.string if soup.title else url

            combined_meta = {"url": url, "title": title}
            if metadata:
                combined_meta.update(metadata)

            return self.ingest_text(text, source=url, metadata=combined_meta)

        except ImportError:
            logger.warning("[KnowledgeIngestor] requests/beautifulsoup4 not installed. Cannot ingest URLs.")
            return {
                "status": "error",
                "error": "URL ingestion requires 'requests' and 'beautifulsoup4' packages.",
                "url": url,
            }
        except Exception as e:
            logger.warning(f"[KnowledgeIngestor] Failed to ingest URL {url}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "url": url,
            }

    # Backward-compatible alias
    def ingest(self, doc: str) -> str:
        """Backward-compatible ingestion method."""
        result = self.ingest_text(doc, source="legacy_ingest")
        return f"[Document indexed: {result.get('chunks_added', 0)} chunks stored]"

    # ------------------------------------------------------------------ #
    #  Retrieval
    # ------------------------------------------------------------------ #

    def search(self, query: str, limit: int = 5) -> List[dict]:
        """
        Search the knowledge base using keyword matching.
        Returns relevant chunks ranked by relevance.
        """
        keywords = set(re.findall(r"\w{3,}", query.lower()))
        if not keywords:
            return []

        scored = []
        for chunk in self._chunks:
            text = chunk.get("text", "").lower()
            tokens = set(re.findall(r"\w{3,}", text))
            if not tokens:
                continue
            overlap = keywords & tokens
            score = len(overlap) / len(keywords)
            if score > 0:
                result = dict(chunk)
                result["_relevance"] = round(score, 3)
                scored.append((score, result))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    # ------------------------------------------------------------------ #
    #  Statistics
    # ------------------------------------------------------------------ #

    def get_knowledge_stats(self) -> dict:
        """Return statistics about the ingested knowledge base."""
        total_chars = sum(len(c.get("text", "")) for c in self._chunks)
        source_counts: Dict[str, int] = {}
        for c in self._chunks:
            src = c.get("source", "unknown")
            source_counts[src] = source_counts.get(src, 0) + 1

        disk_size = 0
        if os.path.exists(self.storage_path):
            disk_size = os.path.getsize(self.storage_path)

        return {
            "total_chunks": len(self._chunks),
            "total_sources": len(self._sources),
            "total_characters": total_chars,
            "source_breakdown": source_counts,
            "disk_size_bytes": disk_size,
            "storage_path": self.storage_path,
        }
