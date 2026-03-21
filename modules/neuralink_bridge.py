"""
Brain-computer interface simulation module.
Simulates neural signals, provides thought-to-command mapping,
neural state visualization, and brainwave decoding.
"""
import random
import time
from datetime import datetime
from collections import deque


class NeuralinkBridge:
    """Simulated brain-computer interface for neural signal processing."""

    BRAINWAVE_BANDS = {
        "delta": (0.5, 4),
        "theta": (4, 8),
        "alpha": (8, 13),
        "beta": (13, 30),
        "gamma": (30, 100),
    }

    THOUGHT_COMMANDS = {
        "focus_buy": {"action": "buy", "confidence_threshold": 0.7},
        "focus_sell": {"action": "sell", "confidence_threshold": 0.7},
        "attention_alert": {"action": "alert", "confidence_threshold": 0.5},
        "calm_hold": {"action": "hold", "confidence_threshold": 0.4},
        "stress_exit": {"action": "emergency_exit", "confidence_threshold": 0.8},
    }

    def __init__(self):
        self.dream_hacking = True
        self.brain_api = "neuralink_v4"
        self.connected = False
        self.neural_history = deque(maxlen=500)
        self.command_log = []
        self.calibration = {"baseline": None, "calibrated": False}

    def connect(self):
        """Establish connection to the neural interface."""
        self.connected = True
        self.calibration["baseline"] = self._generate_baseline()
        self.calibration["calibrated"] = True
        return {"status": "connected", "api": self.brain_api,
                "calibration": "complete", "timestamp": datetime.utcnow().isoformat()}

    def disconnect(self):
        """Disconnect from the neural interface."""
        self.connected = False
        return {"status": "disconnected"}

    def execute_thought(self, brain_signal=None):
        """Decode a brain signal and execute the corresponding command."""
        if not self.connected:
            return {"status": "error", "message": "Neural interface not connected"}

        decoded = self._decode_brain_waves(brain_signal)
        thought_pattern = self._classify_thought(decoded)
        command = self._map_to_command(thought_pattern)

        entry = {
            "decoded": decoded,
            "thought_pattern": thought_pattern,
            "command": command,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.command_log.append(entry)
        self.neural_history.append(decoded)

        if self.dream_hacking and command.get("action") == "buy" and decoded.get("asset") == "BTC":
            self._inject_lucid_dream("BTC long-term bullish scenario")

        return entry

    def _decode_brain_waves(self, signal=None):
        """Decode raw brain wave signals into structured data."""
        if signal and isinstance(signal, dict):
            return signal

        waves = {}
        for band, (low, high) in self.BRAINWAVE_BANDS.items():
            waves[band] = round(random.uniform(0, 1), 3)

        dominant = max(waves, key=waves.get)

        action_map = {
            "gamma": "buy",
            "beta": "analyze",
            "alpha": "hold",
            "theta": "review",
            "delta": "sleep",
        }

        return {
            "action": action_map.get(dominant, "hold"),
            "asset": random.choice(["BTC", "ETH", "SOL", "SPY"]),
            "amount": round(random.uniform(0.01, 2.0), 4),
            "confidence": round(random.uniform(0.3, 1.0), 3),
            "dominant_wave": dominant,
            "wave_powers": waves,
        }

    def _classify_thought(self, decoded):
        """Classify decoded brain activity into a thought pattern."""
        confidence = decoded.get("confidence", 0.5)
        action = decoded.get("action", "hold")
        dominant = decoded.get("dominant_wave", "alpha")

        if dominant == "gamma" and confidence > 0.7:
            return "focus_buy"
        elif dominant == "gamma" and action == "sell":
            return "focus_sell"
        elif dominant == "beta" and confidence > 0.5:
            return "attention_alert"
        elif dominant in ("alpha", "theta"):
            return "calm_hold"
        elif dominant == "delta":
            return "calm_hold"
        return "calm_hold"

    def _map_to_command(self, thought_pattern):
        """Map a thought pattern to an executable command."""
        cmd_template = self.THOUGHT_COMMANDS.get(thought_pattern, {"action": "hold", "confidence_threshold": 0.5})
        return {
            "action": cmd_template["action"],
            "thought_pattern": thought_pattern,
            "confidence_threshold": cmd_template["confidence_threshold"],
        }

    def _generate_baseline(self):
        """Generate a neural baseline for calibration."""
        baseline = {}
        for band in self.BRAINWAVE_BANDS:
            baseline[band] = round(random.uniform(0.2, 0.5), 3)
        return baseline

    def get_neural_state(self):
        """Return current neural state visualization data."""
        if not self.connected:
            return {"status": "disconnected"}

        current = self._decode_brain_waves()
        return {
            "wave_powers": current["wave_powers"],
            "dominant_wave": current["dominant_wave"],
            "focus_level": round(current["wave_powers"].get("gamma", 0) + current["wave_powers"].get("beta", 0), 3),
            "relaxation_level": round(current["wave_powers"].get("alpha", 0) + current["wave_powers"].get("theta", 0), 3),
            "alertness": round(current["confidence"], 3),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _inject_lucid_dream(self, scenario):
        """Simulate lucid dream injection for scenario visualization."""
        entry = {
            "type": "lucid_dream",
            "scenario": scenario,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.command_log.append(entry)

    def get_command_log(self, limit=20):
        """Return recent command history."""
        return self.command_log[-limit:]

    def get_status(self):
        """Return neural bridge status."""
        return {
            "connected": self.connected,
            "api": self.brain_api,
            "calibrated": self.calibration["calibrated"],
            "dream_hacking": self.dream_hacking,
            "total_commands": len(self.command_log),
            "neural_samples": len(self.neural_history),
        }
