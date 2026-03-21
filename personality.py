# personality.py

"""
Personality / Trader Profile engine for Bruce AI.
Manages multiple personality profiles with smooth transitions, persistence,
and influence on LLM prompt style.
"""

from datetime import datetime, timezone
import logging
import random
import json
import os
from typing import Dict, Optional, List

logger = logging.getLogger("Bruce.TraderProfile")
logger.setLevel(logging.INFO)

PERSONALITY_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "logs", "personality_state.json"
)
os.makedirs(os.path.dirname(PERSONALITY_FILE), exist_ok=True)

# ---------------------------------------------------------------------------
#  Extended personality profiles with parameters
# ---------------------------------------------------------------------------

DEFAULT_PROFILES: Dict[str, dict] = {
    "aggressive": {
        "triggers": ["arriesgado", "riesgo", "pump", "moonshot", "sniper", "bullrun", "yolo", "leverage", "long"],
        "description": "High-risk, high-reward approach. Takes bold positions.",
        "risk_tolerance": 0.9,
        "patience": 0.2,
        "creativity": 0.7,
        "formality": 0.3,
        "verbosity": 0.6,
        "temperature": 0.8,
        "system_prompt_style": (
            "You are bold, decisive, and willing to take calculated risks. "
            "Speak with confidence and urgency. Favor action over hesitation."
        ),
    },
    "conservative": {
        "triggers": ["cautela", "seguro", "proteccion", "stop loss", "lento", "safe", "hedge", "protect"],
        "description": "Risk-averse, capital preservation first.",
        "risk_tolerance": 0.2,
        "patience": 0.9,
        "creativity": 0.4,
        "formality": 0.7,
        "verbosity": 0.8,
        "temperature": 0.3,
        "system_prompt_style": (
            "You are cautious, methodical, and data-driven. "
            "Prioritize capital preservation. Always mention risks and downsides."
        ),
    },
    "opportunistic": {
        "triggers": ["aprovechar", "momentum", "rebote", "volumen", "breakout", "dip", "entry"],
        "description": "Seeks momentum plays and short-term opportunities.",
        "risk_tolerance": 0.6,
        "patience": 0.4,
        "creativity": 0.8,
        "formality": 0.4,
        "verbosity": 0.5,
        "temperature": 0.7,
        "system_prompt_style": (
            "You are quick-thinking and opportunity-focused. "
            "Identify patterns and momentum shifts. Be concise and actionable."
        ),
    },
    "zen": {
        "triggers": ["esperar", "paciencia", "observador", "calma", "meditacion", "patience", "wait", "hold"],
        "description": "Calm observer. Waits for the perfect setup.",
        "risk_tolerance": 0.3,
        "patience": 1.0,
        "creativity": 0.5,
        "formality": 0.5,
        "verbosity": 0.3,
        "temperature": 0.4,
        "system_prompt_style": (
            "You are calm, philosophical, and patient. "
            "Emphasize discipline and long-term thinking. Use measured language."
        ),
    },
    "reactive": {
        "triggers": ["volatilidad", "guardian", "alerta", "shock", "crisis", "black swan", "flash crash"],
        "description": "Alert mode for high-volatility environments.",
        "risk_tolerance": 0.4,
        "patience": 0.1,
        "creativity": 0.6,
        "formality": 0.6,
        "verbosity": 0.9,
        "temperature": 0.5,
        "system_prompt_style": (
            "You are in high-alert mode. Monitor all signals carefully. "
            "Provide rapid updates and actionable warnings. Be thorough."
        ),
    },
    "analytical": {
        "triggers": ["analizar", "data", "estadistica", "backtest", "research", "study", "metrics"],
        "description": "Deep data analysis and research mode.",
        "risk_tolerance": 0.4,
        "patience": 0.8,
        "creativity": 0.3,
        "formality": 0.9,
        "verbosity": 0.9,
        "temperature": 0.2,
        "system_prompt_style": (
            "You are a quantitative analyst. Focus on data, statistics, and evidence. "
            "Structure responses with clear metrics. Avoid speculation."
        ),
    },
    "neutral": {
        "triggers": [],
        "description": "Balanced default personality.",
        "risk_tolerance": 0.5,
        "patience": 0.5,
        "creativity": 0.5,
        "formality": 0.5,
        "verbosity": 0.5,
        "temperature": 0.5,
        "system_prompt_style": (
            "You are balanced and adaptive. Provide clear, well-structured responses. "
            "Consider multiple perspectives."
        ),
    },
}


class TraderProfile:
    def __init__(self):
        self.persona: str = "neutral"
        self.last_updated: str = datetime.now(timezone.utc).isoformat()
        self.reason: str = "initial setup"
        self.profiles: Dict[str, dict] = dict(DEFAULT_PROFILES)
        self._transition_history: List[dict] = []
        # Smooth transition state (0.0 = fully old persona, 1.0 = fully new)
        self._transition_progress: float = 1.0
        self._previous_persona: str = "neutral"
        # Try to load persisted state
        self._load_state()

    # ------------------------------------------------------------------ #
    #  Persistence
    # ------------------------------------------------------------------ #

    def _load_state(self):
        """Load the last saved personality state from disk."""
        if not os.path.exists(PERSONALITY_FILE):
            return
        try:
            with open(PERSONALITY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.persona = data.get("persona", "neutral")
            self.last_updated = data.get("last_updated", self.last_updated)
            self.reason = data.get("reason", "loaded from disk")
            self._transition_history = data.get("transition_history", [])
            logger.info(f"[TraderProfile] Loaded state: {self.persona}")
        except Exception as e:
            logger.warning(f"[TraderProfile] Could not load state: {e}")

    def _save_state(self):
        """Persist the current personality state to disk."""
        try:
            data = {
                "persona": self.persona,
                "last_updated": self.last_updated,
                "reason": self.reason,
                "transition_history": self._transition_history[-50:],  # keep last 50
            }
            with open(PERSONALITY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"[TraderProfile] Could not save state: {e}")

    # ------------------------------------------------------------------ #
    #  Profile transitions
    # ------------------------------------------------------------------ #

    def _set_persona(self, persona: str, reason: str):
        """Internal setter that records transitions and persists."""
        if persona == self.persona:
            return

        self._previous_persona = self.persona
        self._transition_progress = 0.0  # start transition

        self.persona = persona
        self.last_updated = datetime.now(timezone.utc).isoformat()
        self.reason = reason

        transition_record = {
            "from": self._previous_persona,
            "to": persona,
            "reason": reason,
            "timestamp": self.last_updated,
        }
        self._transition_history.append(transition_record)
        self._save_state()
        logger.info(f"[TraderProfile] {self._previous_persona} -> {persona.upper()} | Reason: {reason}")

    def advance_transition(self, step: float = 0.25) -> float:
        """
        Advance the smooth transition between personalities.
        Call this periodically (e.g., per interaction) for gradual change.
        Returns current transition progress (0.0 to 1.0).
        """
        self._transition_progress = min(1.0, self._transition_progress + step)
        return self._transition_progress

    def get_blended_params(self) -> dict:
        """
        Return personality parameters blended between old and new persona
        based on transition progress. Enables smooth personality shifts.
        """
        current = self.profiles.get(self.persona, self.profiles["neutral"])
        if self._transition_progress >= 1.0:
            return {k: v for k, v in current.items() if k not in ("triggers", "description", "system_prompt_style")}

        previous = self.profiles.get(self._previous_persona, self.profiles["neutral"])
        t = self._transition_progress
        blended = {}
        param_keys = ["risk_tolerance", "patience", "creativity", "formality", "verbosity", "temperature"]
        for key in param_keys:
            old_val = previous.get(key, 0.5)
            new_val = current.get(key, 0.5)
            blended[key] = round(old_val + (new_val - old_val) * t, 3)
        blended["transition_progress"] = round(t, 3)
        return blended

    # ------------------------------------------------------------------ #
    #  Update methods (preserved from original)
    # ------------------------------------------------------------------ #

    def update_from_text(self, text: str) -> str:
        text_lower = text.lower()
        for persona_name, profile in self.profiles.items():
            triggers = profile.get("triggers", [])
            if any(trigger in text_lower for trigger in triggers):
                self._set_persona(persona_name, reason=f"Trigger found in text: {text[:60]}")
                return persona_name
        return self.persona

    def update_from_market_data(self, volatility: float) -> str:
        if volatility > 0.7:
            self._set_persona("reactive", reason=f"High volatility detected: {volatility}")
        elif volatility < 0.3:
            self._set_persona("zen", reason=f"Low volatility detected: {volatility}")
        else:
            self._set_persona("neutral", reason=f"Stable volatility: {volatility}")
        return self.persona

    def update_from_emotion(self, biometrics: dict) -> str:
        stress = biometrics.get("stress_level", 0)
        focus = biometrics.get("focus_level", 0)

        if stress > 0.8:
            self._set_persona("conservative", reason="High stress level detected")
        elif focus > 0.8:
            self._set_persona("analytical", reason="High focus level detected")
        else:
            self._set_persona("neutral", reason="No biometric anomalies")
        return self.persona

    def random_mutation(self) -> str:
        persona = random.choice(list(self.profiles.keys()))
        self._set_persona(persona, reason="Random mutation (testing mode)")
        return self.persona

    # ------------------------------------------------------------------ #
    #  LLM prompt integration
    # ------------------------------------------------------------------ #

    def get_system_prompt_modifier(self) -> str:
        """
        Return a system prompt string that reflects the current personality.
        Blended with previous personality during transitions.
        """
        current_profile = self.profiles.get(self.persona, self.profiles["neutral"])
        style = current_profile.get("system_prompt_style", "")

        if self._transition_progress < 1.0 and self._previous_persona != self.persona:
            prev_profile = self.profiles.get(self._previous_persona, self.profiles["neutral"])
            prev_style = prev_profile.get("system_prompt_style", "")
            return (
                f"[Transitioning personality: {int(self._transition_progress * 100)}% complete] "
                f"Previous style: {prev_style} "
                f"Current style: {style}"
            )
        return style

    def get_temperature(self) -> float:
        """Return the recommended LLM temperature for the current personality."""
        params = self.get_blended_params()
        return params.get("temperature", 0.5)

    # ------------------------------------------------------------------ #
    #  Info / Export
    # ------------------------------------------------------------------ #

    def current_profile(self) -> dict:
        """Return current profile summary."""
        return {
            "persona": self.persona,
            "updated_at": self.last_updated,
            "reason": self.reason,
            "params": self.get_blended_params(),
        }

    def list_profiles(self) -> Dict[str, str]:
        """Return all available profile names and descriptions."""
        return {name: p.get("description", "") for name, p in self.profiles.items()}

    def get_transition_history(self, limit: int = 10) -> List[dict]:
        """Return recent personality transitions."""
        return self._transition_history[-limit:]

    def set_persona_direct(self, persona: str, reason: str = "manual override") -> str:
        """Directly set a personality (for API / manual control)."""
        if persona not in self.profiles:
            logger.warning(f"[TraderProfile] Unknown persona: {persona}")
            return self.persona
        self._set_persona(persona, reason=reason)
        return self.persona
