# vector_logger.py

import uuid
import datetime
from datetime import timezone
import json
from typing import Optional, Dict, Any, List


class VectorLogEntry:
    """
    🧠 VectorLogEntry – Represents a single interaction, thought, or action in Bruce's vector memory.
    """
    def __init__(self, 
                 role: str,
                 content: str,
                 context: Optional[str] = None,
                 model: Optional[str] = None,
                 tags: Optional[List[str]] = None):
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.datetime.now(timezone.utc).isoformat() + "Z"
        self.role = role  # "user", "assistant", "system", etc.
        self.content = content
        self.context = context or "general"
        self.model = model or "unspecified"
        self.tags = tags or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "role": self.role,
            "content": self.content,
            "context": self.context,
            "model": self.model,
            "tags": self.tags
        }


class VectorLogger:
    """
    📓 VectorLogger – Advanced memory logger for Bruce's cognitive tracking, tactical recall, and training.
    """

    def __init__(self, storage_file: str = "logs/vector_memory.jsonl"):
        self.storage_file = storage_file
        self.log_buffer: List[Dict[str, Any]] = []

    def log(self, entry: VectorLogEntry):
        """
        Log a new vector memory entry to the internal buffer and persistent file.
        """
        log_data = entry.to_dict()
        self.log_buffer.append(log_data)
        self._persist(log_data)

    def _persist(self, data: Dict[str, Any]):
        """
        Write a single log entry to the persistent storage.
        """
        try:
            with open(self.storage_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[VectorLogger] ⚠️ Failed to persist log: {e}")

    def get_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve the most recent 'n' vector logs from memory buffer.
        """
        return self.log_buffer[-limit:]

    def clear_memory(self):
        """
        Clear all in-memory logs (useful during session resets or stealth mode).
        """
        self.log_buffer = []

    def load_logs_from_disk(self) -> List[Dict[str, Any]]:
        """
        Load all logs from disk into memory (use with caution for large files).
        """
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                return [json.loads(line.strip()) for line in f.readlines()]
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"[VectorLogger] ⚠️ Error loading logs: {e}")
            return []

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search through vector logs for a given keyword.
        """
        return [log for log in self.log_buffer if keyword.lower() in log["content"].lower()]
