"""
Avatar materialization module.
Manages physical appearance parameters, animation states,
expression mapping, and avatar configuration.
"""
import random
from datetime import datetime


class PhysicalAvatar:
    """Avatar system with configurable appearance, animation, and expressions."""

    LOCATIONS = {
        "nyse": {"persona": "Wall Street Analyst", "style": "formal_suit", "aura": "golden"},
        "opec": {"persona": "Energy Strategist", "style": "diplomatic", "aura": "emerald"},
        "silicon_valley": {"persona": "Tech Visionary", "style": "smart_casual", "aura": "electric_blue"},
        "tokyo": {"persona": "Quantitative Trader", "style": "minimalist", "aura": "neon"},
        "london": {"persona": "Fund Manager", "style": "bespoke_suit", "aura": "silver"},
        "zurich": {"persona": "Private Banker", "style": "conservative", "aura": "platinum"},
    }

    EXPRESSIONS = {
        "confident": {"posture": "upright", "gaze": "direct", "gesture": "open_hands"},
        "analytical": {"posture": "leaning_forward", "gaze": "focused", "gesture": "chin_rest"},
        "cautious": {"posture": "reserved", "gaze": "scanning", "gesture": "crossed_arms"},
        "excited": {"posture": "energetic", "gaze": "wide", "gesture": "animated"},
        "calm": {"posture": "relaxed", "gaze": "steady", "gesture": "still"},
        "authoritative": {"posture": "commanding", "gaze": "piercing", "gesture": "steepled_fingers"},
    }

    ANIMATION_STATES = ["idle", "speaking", "analyzing", "trading", "presenting", "listening"]

    def __init__(self):
        self.current_location = None
        self.current_expression = "calm"
        self.animation_state = "idle"
        self.appearance = {
            "height_cm": 185,
            "build": "athletic",
            "hair": "dark",
            "attire": "formal_suit",
            "accessories": ["watch", "earpiece"],
        }
        self.state_history = []

    def materialize(self, location):
        """Materialize avatar at a specific location with appropriate persona."""
        loc_key = location.lower().replace(" ", "_")
        loc_config = self.LOCATIONS.get(loc_key)

        if loc_config:
            self.current_location = loc_key
            self.appearance["attire"] = loc_config["style"]
            entry = {
                "location": loc_key,
                "persona": loc_config["persona"],
                "style": loc_config["style"],
                "aura": loc_config["aura"],
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            self.current_location = loc_key
            entry = {
                "location": loc_key,
                "persona": "Generic Cognition Agent",
                "style": self.appearance["attire"],
                "aura": "neutral",
                "timestamp": datetime.utcnow().isoformat(),
            }

        self.state_history.append(entry)
        return entry

    def set_expression(self, expression):
        """Set the avatar's current facial/body expression."""
        if expression not in self.EXPRESSIONS:
            return {"status": "error", "message": f"Unknown expression: {expression}",
                    "available": list(self.EXPRESSIONS.keys())}
        self.current_expression = expression
        return {"expression": expression, "details": self.EXPRESSIONS[expression]}

    def set_animation(self, state):
        """Set the avatar's animation state."""
        if state not in self.ANIMATION_STATES:
            return {"status": "error", "message": f"Unknown state: {state}",
                    "available": self.ANIMATION_STATES}
        self.animation_state = state
        return {"animation_state": state}

    def update_appearance(self, **kwargs):
        """Update appearance parameters."""
        updated = {}
        for key, value in kwargs.items():
            if key in self.appearance:
                self.appearance[key] = value
                updated[key] = value
        return {"updated": updated, "appearance": self.appearance}

    def get_current_state(self):
        """Return complete current avatar state."""
        return {
            "location": self.current_location,
            "expression": self.current_expression,
            "expression_details": self.EXPRESSIONS.get(self.current_expression, {}),
            "animation_state": self.animation_state,
            "appearance": self.appearance,
            "location_config": self.LOCATIONS.get(self.current_location),
        }

    def get_available_locations(self):
        """Return available materialization locations."""
        return self.LOCATIONS

    def get_state_history(self, limit=20):
        """Return recent state changes."""
        return self.state_history[-limit:]
