"""
Synchronization module for inter-instance cognitive alignment.
Handles export/import of memory state, conflict resolution,
and sync status tracking across Bruce instances.
"""
import socket
import json
import hashlib
import time
from datetime import datetime


class CognitiveSync:
    """Memory synchronization between multiple Bruce instances."""

    def __init__(self, peers=None):
        self.peers = peers or []
        self.local_memory = {}
        self.sync_log = []
        self.conflict_history = []
        self.version_counter = 0
        self.instance_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

    def broadcast_memory(self, memory_chunk):
        """Broadcast a memory chunk to all peer instances."""
        versioned_chunk = self._version_stamp(memory_chunk)
        results = {}
        for peer in self.peers:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)
                    s.connect((peer["host"], peer["port"]))
                    s.sendall(json.dumps(versioned_chunk).encode("utf-8"))
                    results[f"{peer['host']}:{peer['port']}"] = "sent"
                    self.sync_log.append({
                        "action": "broadcast",
                        "peer": f"{peer['host']}:{peer['port']}",
                        "status": "success",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
            except Exception as e:
                results[f"{peer['host']}:{peer['port']}"] = f"failed: {e}"
                self.sync_log.append({
                    "action": "broadcast",
                    "peer": f"{peer['host']}:{peer['port']}",
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                })
        return results

    def receive_and_integrate(self, data):
        """Receive and integrate shared memory from another instance."""
        if not isinstance(data, dict):
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return {"status": "error", "message": "Invalid data format"}

        conflicts = self._detect_conflicts(data)
        if conflicts:
            resolved = self._resolve_conflicts(conflicts, data)
            self.conflict_history.extend(resolved)

        for key, value in data.items():
            if key.startswith("_meta_"):
                continue
            self.local_memory[key] = value

        self.sync_log.append({
            "action": "integrate",
            "keys_received": len(data),
            "conflicts": len(conflicts),
            "timestamp": datetime.utcnow().isoformat(),
        })
        return {"status": "integrated", "keys": len(data), "conflicts_resolved": len(conflicts)}

    def export_memory(self, keys=None):
        """Export local memory state, optionally filtered by keys."""
        if keys:
            export = {k: self.local_memory[k] for k in keys if k in self.local_memory}
        else:
            export = self.local_memory.copy()
        return self._version_stamp(export)

    def import_memory(self, memory_state):
        """Import a full memory state, overwriting local memory."""
        if "_meta_version" in memory_state:
            if memory_state["_meta_version"] <= self.version_counter:
                return {"status": "skipped", "reason": "stale version"}
        return self.receive_and_integrate(memory_state)

    def _version_stamp(self, chunk):
        """Add version metadata to a memory chunk."""
        self.version_counter += 1
        chunk["_meta_version"] = self.version_counter
        chunk["_meta_instance"] = self.instance_id
        chunk["_meta_timestamp"] = datetime.utcnow().isoformat()
        return chunk

    def _detect_conflicts(self, incoming_data):
        """Detect conflicts between incoming and local memory."""
        conflicts = []
        for key, value in incoming_data.items():
            if key.startswith("_meta_"):
                continue
            if key in self.local_memory and self.local_memory[key] != value:
                conflicts.append({
                    "key": key,
                    "local_value": self.local_memory[key],
                    "incoming_value": value,
                })
        return conflicts

    def _resolve_conflicts(self, conflicts, incoming_data):
        """Resolve conflicts using last-write-wins strategy."""
        resolved = []
        incoming_version = incoming_data.get("_meta_version", 0)
        for conflict in conflicts:
            if incoming_version >= self.version_counter:
                resolution = "accept_incoming"
                self.local_memory[conflict["key"]] = conflict["incoming_value"]
            else:
                resolution = "keep_local"
            resolved.append({
                "key": conflict["key"],
                "resolution": resolution,
                "timestamp": datetime.utcnow().isoformat(),
            })
        return resolved

    def add_peer(self, host, port):
        """Add a new peer instance."""
        peer = {"host": host, "port": port}
        if peer not in self.peers:
            self.peers.append(peer)
        return {"peers": len(self.peers)}

    def remove_peer(self, host, port):
        """Remove a peer instance."""
        self.peers = [p for p in self.peers if not (p["host"] == host and p["port"] == port)]
        return {"peers": len(self.peers)}

    def get_sync_status(self):
        """Return current sync status."""
        return {
            "instance_id": self.instance_id,
            "version": self.version_counter,
            "peers": len(self.peers),
            "local_memory_keys": len(self.local_memory),
            "total_syncs": len(self.sync_log),
            "conflicts_resolved": len(self.conflict_history),
            "recent_syncs": self.sync_log[-5:],
        }

    def store(self, key, value):
        """Store a value in local memory."""
        self.local_memory[key] = value
        self.version_counter += 1
        return {"stored": key, "version": self.version_counter}

    def retrieve(self, key, default=None):
        """Retrieve a value from local memory."""
        return self.local_memory.get(key, default)
