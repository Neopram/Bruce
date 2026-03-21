
# memory.py
"""
MemoryManager - Manages interaction memory with JSONL persistence and in-memory indexing.
Supports logging, recall, keyword search, decision storage, and memory statistics.
"""

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger("Bruce.Memory")
logger.setLevel(logging.INFO)

MEMORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
MEMORY_FILE = os.path.join(MEMORY_DIR, "memory.jsonl")


class MemoryManager:
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or MEMORY_FILE
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        # In-memory index: user_id -> list of interaction dicts
        self.logs: Dict[str, List[dict]] = {}
        # Load existing data from disk
        self._load_from_disk()

    # ------------------------------------------------------------------ #
    #  Persistence helpers
    # ------------------------------------------------------------------ #

    def _load_from_disk(self):
        """Load all persisted interactions into the in-memory index."""
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        user = entry.get("user_id", "unknown")
                        self.logs.setdefault(user, []).append(entry)
                    except json.JSONDecodeError:
                        continue
            logger.info(f"[Memory] Loaded {sum(len(v) for v in self.logs.values())} entries from disk")
        except Exception as e:
            logger.warning(f"[Memory] Could not load from disk: {e}")

    def _persist(self, entry: dict):
        """Append a single entry to the JSONL file."""
        try:
            with open(self.storage_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"[Memory] Could not persist entry: {e}")

    # ------------------------------------------------------------------ #
    #  Core API
    # ------------------------------------------------------------------ #

    def log_interaction(self, prompt: str, user: str, metadata: Optional[dict] = None):
        """
        Log an interaction (user input) with optional metadata.
        Stores both in-memory and on disk.
        """
        entry = {
            "type": "interaction",
            "prompt": prompt,
            "user_id": user,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.logs.setdefault(user, []).append(entry)
        self._persist(entry)
        logger.info(f"[Memory] Logged interaction for user={user}")
        return entry

    def store_decision(self, prompt: str, decision: Any, user: str):
        """
        Store a decision record tied to a prompt.
        """
        entry = {
            "type": "decision",
            "prompt": prompt,
            "decision": decision if isinstance(decision, (str, int, float, bool)) else str(decision),
            "user_id": user,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.logs.setdefault(user, []).append(entry)
        self._persist(entry)
        logger.info(f"[Memory] Stored decision for user={user}")
        return entry

    def recall(self, user: str, limit: int = 5) -> List[dict]:
        """
        Return the most recent interactions for a user.
        """
        entries = self.logs.get(user, [])
        return entries[-limit:] if entries else []

    def search(self, query: str, user: str, limit: int = 5) -> List[dict]:
        """
        Semantic search over a user's memory.
        Uses basic keyword matching as a fallback when FAISS/embeddings are not available.
        Each result receives a relevance score (0-1).
        """
        entries = self.logs.get(user, [])
        if not entries:
            return []

        # Tokenize query into lowercase keywords
        keywords = set(re.findall(r"\w+", query.lower()))
        if not keywords:
            return self.recall(user, limit)

        scored: List[tuple] = []
        for entry in entries:
            # Build searchable text from all string fields
            searchable_parts = []
            for key in ("prompt", "decision", "type"):
                val = entry.get(key, "")
                if isinstance(val, str):
                    searchable_parts.append(val.lower())
            # Also search metadata values
            meta = entry.get("metadata", {})
            if isinstance(meta, dict):
                for v in meta.values():
                    if isinstance(v, str):
                        searchable_parts.append(v.lower())

            text = " ".join(searchable_parts)
            text_tokens = set(re.findall(r"\w+", text))

            if not text_tokens:
                continue

            # Compute overlap score
            overlap = keywords & text_tokens
            score = len(overlap) / len(keywords)
            if score > 0:
                scored.append((score, entry))

        # Sort by score descending, then by timestamp descending
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, entry in scored[:limit]:
            result = dict(entry)
            result["_relevance"] = round(score, 3)
            results.append(result)
        return results

    def summarize(self) -> str:
        """
        Produce a summary of all stored memory across all users.
        """
        total_entries = sum(len(v) for v in self.logs.values())
        user_count = len(self.logs)
        if total_entries == 0:
            return "No interactions stored yet."

        decision_count = 0
        interaction_count = 0
        for entries in self.logs.values():
            for e in entries:
                if e.get("type") == "decision":
                    decision_count += 1
                else:
                    interaction_count += 1

        lines = [
            f"Memory summary: {total_entries} total entries across {user_count} user(s).",
            f"  - Interactions: {interaction_count}",
            f"  - Decisions: {decision_count}",
        ]

        # Show last entry timestamp per user
        for user, entries in self.logs.items():
            if entries:
                last_ts = entries[-1].get("timestamp", "unknown")
                lines.append(f"  - User '{user}': {len(entries)} entries, last at {last_ts}")

        return "\n".join(lines)

    def clear(self, user: str):
        """
        Clear all memory for a specific user (in-memory and on disk).
        Rewrites the JSONL file excluding the user's entries.
        """
        removed_count = len(self.logs.pop(user, []))
        # Rewrite disk file without this user's entries
        self._rewrite_disk()
        logger.info(f"[Memory] Cleared {removed_count} entries for user={user}")
        return {"cleared": removed_count, "user": user}

    def _rewrite_disk(self):
        """Rewrite the JSONL file from current in-memory state."""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                for entries in self.logs.values():
                    for entry in entries:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"[Memory] Could not rewrite disk: {e}")

    def get_stats(self) -> dict:
        """
        Return memory statistics.
        """
        total = sum(len(v) for v in self.logs.values())
        per_user = {user: len(entries) for user, entries in self.logs.items()}
        type_counts: Dict[str, int] = {}
        for entries in self.logs.values():
            for e in entries:
                t = e.get("type", "unknown")
                type_counts[t] = type_counts.get(t, 0) + 1

        disk_size = 0
        if os.path.exists(self.storage_path):
            disk_size = os.path.getsize(self.storage_path)

        return {
            "total_entries": total,
            "user_count": len(self.logs),
            "per_user": per_user,
            "type_counts": type_counts,
            "disk_size_bytes": disk_size,
            "storage_path": self.storage_path,
        }
