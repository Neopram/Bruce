
"""
memory_engine.py - Episodic memory engine for Bruce.
Manages episode-based memory with persistence, retrieval, context building,
pruning, and export capabilities.
"""

import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import re
import logging

logger = logging.getLogger("Bruce.MemoryEngine")
logger.setLevel(logging.INFO)


class EpisodicMemory:
    """Manages episode-based memory with JSONL persistence."""

    def __init__(self, path: str = "./logs/episodes.jsonl"):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._index: Dict[str, List[dict]] = {}  # user_id -> episodes
        self._load_index()

    def _load_index(self):
        """Load all episodes into the in-memory index on startup."""
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        episode = json.loads(line)
                        user_id = episode.get("user_id", "system")
                        self._index.setdefault(user_id, []).append(episode)
                    except json.JSONDecodeError:
                        continue
            total = sum(len(v) for v in self._index.values())
            logger.info(f"[EpisodicMemory] Loaded {total} episodes from disk")
        except Exception as e:
            logger.warning(f"[EpisodicMemory] Could not load index: {e}")

    def _persist(self, episode: dict):
        """Append a single episode to the JSONL file."""
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(episode, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"[EpisodicMemory] Could not persist episode: {e}")

    def _rewrite_disk(self):
        """Rewrite the entire JSONL file from the in-memory index."""
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                for episodes in self._index.values():
                    for ep in episodes:
                        f.write(json.dumps(ep, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"[EpisodicMemory] Could not rewrite disk: {e}")

    # ------------------------------------------------------------------ #
    #  Core API
    # ------------------------------------------------------------------ #

    def store_episode(self, episode_data: dict) -> dict:
        """
        Store an episode with automatic timestamping.
        episode_data should contain at minimum: user_id, input, and optionally tags, context, etc.
        """
        episode = dict(episode_data)
        episode.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        episode.setdefault("user_id", "system")
        episode.setdefault("tags", [])

        user_id = episode["user_id"]
        self._index.setdefault(user_id, []).append(episode)
        self._persist(episode)
        logger.info(f"[EpisodicMemory] Stored episode for user={user_id}")
        return episode

    # Backward-compatible alias
    def save_episode(self, episode_data: dict):
        """Alias for store_episode (backward compatibility)."""
        return self.store_episode(episode_data)

    def get_episodes(self, user_id: str, limit: int = 10) -> List[dict]:
        """Retrieve the most recent episodes for a user."""
        episodes = self._index.get(user_id, [])
        return episodes[-limit:]

    def get_context(self, user_id: str, query: str, limit: int = 5) -> List[dict]:
        """
        Retrieve episodes relevant to a query for context building.
        Uses keyword matching to score relevance.
        """
        episodes = self._index.get(user_id, [])
        if not episodes:
            return []

        keywords = set(re.findall(r"\w+", query.lower()))
        if not keywords:
            return episodes[-limit:]

        scored = []
        for ep in episodes:
            # Build searchable text from episode fields
            parts = []
            for key in ("input", "output", "decision", "reflection", "summary"):
                val = ep.get(key, "")
                if isinstance(val, str):
                    parts.append(val.lower())
            # Include tags
            for tag in ep.get("tags", []):
                if isinstance(tag, str):
                    parts.append(tag.lower())

            text = " ".join(parts)
            tokens = set(re.findall(r"\w+", text))
            if not tokens:
                continue

            overlap = keywords & tokens
            score = len(overlap) / len(keywords)
            if score > 0:
                scored.append((score, ep))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored[:limit]]

    # Backward-compatible alias
    def retrieve_context(self, tag: str = "train", limit: int = 5) -> List[dict]:
        """
        Retrieve episodes matching a tag string (backward compatibility).
        Falls back to searching the input field.
        """
        if not os.path.exists(self.path):
            return []

        context = []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in reversed(f.readlines()):
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    # Check tags list or input text
                    tags = data.get("tags", [])
                    input_text = data.get("input", "")
                    if tag in tags or tag in input_text:
                        context.append(data)
                        if len(context) >= limit:
                            break
        except Exception:
            pass
        return context

    def prune(self, max_age_days: int = 30) -> dict:
        """
        Remove episodes older than max_age_days.
        Returns a summary of what was pruned.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        cutoff_iso = cutoff.isoformat()

        total_pruned = 0
        for user_id in list(self._index.keys()):
            before = len(self._index[user_id])
            self._index[user_id] = [
                ep for ep in self._index[user_id]
                if ep.get("timestamp", "") >= cutoff_iso
            ]
            pruned = before - len(self._index[user_id])
            total_pruned += pruned
            # Remove empty user entries
            if not self._index[user_id]:
                del self._index[user_id]

        if total_pruned > 0:
            self._rewrite_disk()
            logger.info(f"[EpisodicMemory] Pruned {total_pruned} episodes older than {max_age_days} days")

        return {
            "pruned": total_pruned,
            "max_age_days": max_age_days,
            "cutoff": cutoff_iso,
        }

    def export_episodes(self, user_id: str, fmt: str = "json") -> str:
        """
        Export a user's episodes to a string in the requested format.
        Supported formats: 'json', 'jsonl', 'summary'.
        """
        episodes = self._index.get(user_id, [])

        if fmt == "jsonl":
            return "\n".join(json.dumps(ep, ensure_ascii=False) for ep in episodes)
        elif fmt == "summary":
            lines = [f"Episodes for user '{user_id}': {len(episodes)} total"]
            for i, ep in enumerate(episodes, 1):
                ts = ep.get("timestamp", "?")
                inp = ep.get("input", ep.get("summary", ""))
                preview = inp[:80] + "..." if len(inp) > 80 else inp
                lines.append(f"  {i}. [{ts}] {preview}")
            return "\n".join(lines)
        else:  # json
            return json.dumps(episodes, ensure_ascii=False, indent=2)

    def get_stats(self) -> dict:
        """Return statistics about the episodic memory store."""
        total = sum(len(v) for v in self._index.values())
        disk_size = 0
        if os.path.exists(self.path):
            disk_size = os.path.getsize(self.path)
        return {
            "total_episodes": total,
            "user_count": len(self._index),
            "per_user": {u: len(eps) for u, eps in self._index.items()},
            "disk_size_bytes": disk_size,
            "storage_path": self.path,
        }


# Backward-compatible alias
MemoryEngine = EpisodicMemory
