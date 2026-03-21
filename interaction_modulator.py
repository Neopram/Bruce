# Modula la interaccion con el usuario
import re
from collections import defaultdict


class InteractionModulator:
    """Adjusts AI responses based on user context, urgency, and communication preferences."""

    URGENCY_KEYWORDS = [
        "urgent", "asap", "immediately", "emergency", "critical", "crash",
        "down", "failing", "broken", "help", "now", "quick", "hurry", "fast",
        "alert", "danger", "risk", "loss", "liquidat",
    ]

    VERBOSITY_LEVELS = {"brief": 0.3, "normal": 1.0, "detailed": 1.5, "verbose": 2.0}

    def __init__(self):
        self._user_styles = defaultdict(lambda: {
            "verbosity": "normal",
            "formality": "neutral",
            "interaction_count": 0,
            "preferred_topics": [],
        })

    def modulate(self, response, context):
        """Adjust response based on context dict (stress_level, user_id, urgency, verbosity)."""
        stress = context.get("stress_level", 0)
        user_id = context.get("user_id")
        urgency = context.get("urgency", False)
        verbosity = context.get("verbosity", "normal")

        if user_id:
            self._user_styles[user_id]["interaction_count"] += 1

        if stress > 0.7 or urgency:
            response = self._add_reassurance(response)
            response = self.adjust_verbosity(response, "brief")
        else:
            response = self.adjust_verbosity(response, verbosity)

        if stress > 0.5:
            response = self._soften_language(response)

        return response

    def detect_urgency(self, query):
        """Detect if a query is urgent. Returns dict with is_urgent bool and score 0-1."""
        query_lower = query.lower()
        matches = [kw for kw in self.URGENCY_KEYWORDS if kw in query_lower]
        exclamation_count = query.count("!")
        caps_ratio = sum(1 for c in query if c.isupper()) / max(len(query), 1)

        score = min(1.0, (len(matches) * 0.2) + (exclamation_count * 0.1) + (caps_ratio * 0.3))
        return {
            "is_urgent": score >= 0.4,
            "score": round(score, 3),
            "matched_keywords": matches,
        }

    def adjust_verbosity(self, response, level):
        """Adjust response length based on verbosity level."""
        factor = self.VERBOSITY_LEVELS.get(level, 1.0)
        sentences = re.split(r'(?<=[.!?])\s+', response.strip())
        if not sentences:
            return response

        if factor < 1.0:
            keep = max(1, int(len(sentences) * factor))
            return " ".join(sentences[:keep])
        elif factor > 1.0:
            return response
        return response

    def get_communication_style(self, user_id):
        """Return learned communication style preferences for a user."""
        style = dict(self._user_styles[user_id])
        style["user_id"] = user_id
        return style

    def set_communication_style(self, user_id, **kwargs):
        """Update communication style preferences for a user."""
        style = self._user_styles[user_id]
        for key in ("verbosity", "formality", "preferred_topics"):
            if key in kwargs:
                style[key] = kwargs[key]
        return self.get_communication_style(user_id)

    def _add_reassurance(self, response):
        """Prepend calming language for urgent/high-stress situations."""
        prefix = "I'm on it. "
        return prefix + response

    def _soften_language(self, response):
        """Replace harsh phrasing with softer alternatives."""
        replacements = {
            "you must": "you might want to",
            "you need to": "it would help to",
            "failure": "issue",
            "wrong": "not quite right",
            "error": "hiccup",
        }
        result = response
        for harsh, soft in replacements.items():
            result = re.sub(re.escape(harsh), soft, result, flags=re.IGNORECASE)
        return result
