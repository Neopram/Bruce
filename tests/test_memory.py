"""Tests for memory.py - MemoryManager."""

import os
import sys
import json
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from memory import MemoryManager


class TestMemoryManager:
    """Tests for the MemoryManager class."""

    @pytest.fixture(autouse=True)
    def _setup(self, temp_dir):
        """Create a fresh MemoryManager with temp storage for each test."""
        self.storage_path = os.path.join(temp_dir, "test_memory.jsonl")
        self.mm = MemoryManager(storage_path=self.storage_path)

    def test_log_interaction(self):
        """log_interaction stores an entry and returns it."""
        entry = self.mm.log_interaction("Hello Bruce", "user1")
        assert entry["type"] == "interaction"
        assert entry["prompt"] == "Hello Bruce"
        assert entry["user_id"] == "user1"
        assert "timestamp" in entry

    def test_log_interaction_persists_to_disk(self):
        """Logged interactions are written to the JSONL file."""
        self.mm.log_interaction("Test persist", "user1")
        assert os.path.exists(self.storage_path)
        with open(self.storage_path, "r") as f:
            lines = f.readlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["prompt"] == "Test persist"

    def test_log_interaction_with_metadata(self):
        """log_interaction stores optional metadata."""
        meta = {"source": "chat", "model": "phi3"}
        entry = self.mm.log_interaction("With meta", "user1", metadata=meta)
        assert entry["metadata"]["source"] == "chat"
        assert entry["metadata"]["model"] == "phi3"

    def test_recall_returns_recent(self):
        """recall returns the most recent interactions for a user."""
        for i in range(10):
            self.mm.log_interaction(f"Message {i}", "user1")
        results = self.mm.recall("user1", limit=3)
        assert len(results) == 3
        assert results[-1]["prompt"] == "Message 9"
        assert results[0]["prompt"] == "Message 7"

    def test_recall_empty_user(self):
        """recall returns empty list for unknown user."""
        results = self.mm.recall("nonexistent")
        assert results == []

    def test_search_finds_matching_entries(self):
        """search returns entries matching the query keywords."""
        self.mm.log_interaction("Buy Bitcoin now", "user1")
        self.mm.log_interaction("Sell Ethereum quickly", "user1")
        self.mm.log_interaction("Check weather forecast", "user1")

        results = self.mm.search("Bitcoin buy", "user1")
        assert len(results) >= 1
        assert any("Bitcoin" in r["prompt"] for r in results)
        # Each result should have a relevance score
        assert all("_relevance" in r for r in results)

    def test_search_returns_empty_for_no_match(self):
        """search returns empty when no keywords match."""
        self.mm.log_interaction("Hello world", "user1")
        results = self.mm.search("zzzznonexistent", "user1")
        assert results == []

    def test_store_decision(self):
        """store_decision creates a decision-type entry."""
        entry = self.mm.store_decision("Should I buy?", "BUY", "user1")
        assert entry["type"] == "decision"
        assert entry["decision"] == "BUY"
        assert entry["prompt"] == "Should I buy?"

    def test_clear_removes_user_data(self):
        """clear removes all entries for a specific user."""
        self.mm.log_interaction("msg1", "user1")
        self.mm.log_interaction("msg2", "user1")
        self.mm.log_interaction("msg3", "user2")

        result = self.mm.clear("user1")
        assert result["cleared"] == 2
        assert self.mm.recall("user1") == []
        # user2 should be unaffected
        assert len(self.mm.recall("user2")) == 1

    def test_get_stats(self):
        """get_stats returns correct counts."""
        self.mm.log_interaction("msg1", "user1")
        self.mm.store_decision("q", "HOLD", "user1")
        self.mm.log_interaction("msg2", "user2")

        stats = self.mm.get_stats()
        assert stats["total_entries"] == 3
        assert stats["user_count"] == 2
        assert stats["per_user"]["user1"] == 2
        assert stats["per_user"]["user2"] == 1
        assert stats["type_counts"]["interaction"] == 2
        assert stats["type_counts"]["decision"] == 1

    def test_summarize_empty(self):
        """summarize returns a message when no data exists."""
        summary = self.mm.summarize()
        assert "No interactions" in summary

    def test_summarize_with_data(self):
        """summarize returns a formatted summary string."""
        self.mm.log_interaction("msg", "user1")
        self.mm.store_decision("q", "SELL", "user1")
        summary = self.mm.summarize()
        assert "2 total entries" in summary
        assert "1 user" in summary
        assert "Interactions: 1" in summary
        assert "Decisions: 1" in summary

    def test_persistence_across_instances(self, temp_dir):
        """A new MemoryManager instance loads data from the same file."""
        path = os.path.join(temp_dir, "persist_test.jsonl")
        mm1 = MemoryManager(storage_path=path)
        mm1.log_interaction("persistent msg", "user1")

        mm2 = MemoryManager(storage_path=path)
        results = mm2.recall("user1")
        assert len(results) == 1
        assert results[0]["prompt"] == "persistent msg"

    def test_search_with_empty_query(self):
        """search with empty query falls back to recall."""
        self.mm.log_interaction("msg1", "user1")
        self.mm.log_interaction("msg2", "user1")
        results = self.mm.search("", "user1", limit=1)
        assert len(results) == 1
