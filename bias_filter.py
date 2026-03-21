
# bias_filter.py

"""
Bias Filter module for Bruce AI.
Detects cognitive biases in text, flags them, and maintains a bias history
per user for ongoing awareness and improvement.
"""

import re
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("Bruce.BiasFilter")
logger.setLevel(logging.INFO)

BIAS_LOG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "logs", "bias_history.jsonl"
)
os.makedirs(os.path.dirname(BIAS_LOG), exist_ok=True)

# ---------------------------------------------------------------------------
#  Cognitive bias patterns
# ---------------------------------------------------------------------------

BIAS_PATTERNS: Dict[str, dict] = {
    "confirmation_bias": {
        "description": "Tendency to favor information that confirms existing beliefs.",
        "patterns": [
            r"\b(obviously|clearly|everyone knows|as expected|proves? (my|our) point)\b",
            r"\b(i knew it|told you so|just as i thought|confirms? what)\b",
            r"\b(always been right|never wrong)\b",
        ],
        "severity": "high",
        "suggestion": "Consider actively seeking contradicting evidence before concluding.",
    },
    "anchoring_bias": {
        "description": "Over-relying on the first piece of information encountered.",
        "patterns": [
            r"\b(originally|initial(ly)?|first (price|target|estimate)|started at)\b",
            r"\b(compared to (the )?original|from (the )?beginning|anchor(ed)?)\b",
            r"\b(was at \$?\d+|used to be|back when it was)\b",
        ],
        "severity": "medium",
        "suggestion": "Re-evaluate based on current data, not just the initial reference point.",
    },
    "fomo": {
        "description": "Fear of missing out - rushing into decisions due to perceived urgency.",
        "patterns": [
            r"\b(fomo|missing out|left behind|too late|hurry|last chance)\b",
            r"\b(everyone (is|already)|don'?t miss|limited time|act now)\b",
            r"\b(going to the moon|gonna pump|about to explode|rocket)\b",
        ],
        "severity": "high",
        "suggestion": "Pause and analyze fundamentals. FOMO-driven decisions often lead to losses.",
    },
    "recency_bias": {
        "description": "Overweighting recent events while ignoring longer-term trends.",
        "patterns": [
            r"\b(just (happened|dropped|pumped|crashed)|today'?s (move|action))\b",
            r"\b(in the last (hour|minute|few)|right now|currently)\b",
            r"\b(this week|latest|most recent|just saw)\b",
        ],
        "severity": "medium",
        "suggestion": "Zoom out to longer timeframes. Recent events may not reflect the full picture.",
    },
    "sunk_cost_fallacy": {
        "description": "Continuing because of past investment rather than future value.",
        "patterns": [
            r"\b(already invested|put (so much|too much)|can'?t sell now)\b",
            r"\b(too late to (exit|sell|stop)|come this far|spent (so|too) much)\b",
            r"\b(average down|hold (the )?bag|diamond hands)\b",
        ],
        "severity": "high",
        "suggestion": "Evaluate the position based on current merit, not past costs.",
    },
    "overconfidence_bias": {
        "description": "Excessive confidence in one's own predictions or abilities.",
        "patterns": [
            r"\b(guaranteed|100%|impossible to (lose|fail)|can'?t go wrong)\b",
            r"\b(sure thing|no way it (fails|drops)|absolutely certain)\b",
            r"\b(trust me|i'?m always right|never been wrong)\b",
        ],
        "severity": "high",
        "suggestion": "No trade is guaranteed. Assign realistic probability ranges.",
    },
    "herd_mentality": {
        "description": "Following the crowd without independent analysis.",
        "patterns": [
            r"\b(everyone (is|says)|the crowd|most people|popular opinion)\b",
            r"\b(trending|viral|hype|bandwagon|consensus)\b",
            r"\b(twitter says|reddit says|influencer|following the trend)\b",
        ],
        "severity": "medium",
        "suggestion": "Form your own thesis. The crowd is often wrong at extremes.",
    },
    "loss_aversion": {
        "description": "Feeling losses more strongly than equivalent gains.",
        "patterns": [
            r"\b(can'?t afford to lose|scared of losing|don'?t want to lose)\b",
            r"\b(protect (my|the) (capital|gains)|fear of loss)\b",
            r"\b(what if (it|i) lose|risk of losing)\b",
        ],
        "severity": "medium",
        "suggestion": "Define acceptable risk upfront. Use stop-losses and position sizing.",
    },
    "survivorship_bias": {
        "description": "Focusing on successes while ignoring failures.",
        "patterns": [
            r"\b(look at (how )?(\w+ )?succeeded|they made (millions|it big))\b",
            r"\b(became? rich|success stor(y|ies)|made it)\b",
            r"\b(if they can|just like (\w+ )?did|follow their path)\b",
        ],
        "severity": "low",
        "suggestion": "Also study failures and the base rate of success in this domain.",
    },
    "gambler_fallacy": {
        "description": "Believing past events affect independent future probabilities.",
        "patterns": [
            r"\b(due for a|overdue|has to (go up|recover|bounce))\b",
            r"\b(can'?t (drop|go down) (again|more|forever))\b",
            r"\b(law of averages|bound to (change|reverse|turn))\b",
        ],
        "severity": "medium",
        "suggestion": "Each event is independent. Past patterns don't guarantee future outcomes.",
    },
}


class BiasFilter:
    def __init__(self):
        self._history: Dict[str, List[dict]] = {}  # user_id -> list of detections
        self._load_history()

    def _load_history(self):
        """Load bias detection history from disk."""
        if not os.path.exists(BIAS_LOG):
            return
        try:
            with open(BIAS_LOG, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        user = rec.get("user_id", "anonymous")
                        self._history.setdefault(user, []).append(rec)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

    def _persist(self, record: dict):
        try:
            with open(BIAS_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  Core detection
    # ------------------------------------------------------------------ #

    def detect_biases(self, text: str) -> List[dict]:
        """
        Detect cognitive biases in the given text.
        Returns a list of detected biases with details.
        """
        text_lower = text.lower()
        detected = []

        for bias_name, bias_info in BIAS_PATTERNS.items():
            for pattern in bias_info["patterns"]:
                try:
                    matches = re.findall(pattern, text_lower, re.IGNORECASE)
                    if matches:
                        # Flatten tuple matches from groups
                        flat_matches = []
                        for m in matches:
                            if isinstance(m, tuple):
                                flat_matches.append(m[0])
                            else:
                                flat_matches.append(m)

                        detected.append({
                            "bias": bias_name,
                            "description": bias_info["description"],
                            "severity": bias_info["severity"],
                            "suggestion": bias_info["suggestion"],
                            "matched_phrases": flat_matches[:3],
                        })
                        break  # one match per bias type is enough
                except re.error:
                    continue

        return detected

    def clean(self, text: str, user_id: str = "anonymous") -> Dict:
        """
        Analyze text for biases and return the original text with bias annotations.
        Does not modify the text content, but flags detected biases.
        Preserves original behavior of returning cleaned text for backward compatibility.
        """
        biases = self.detect_biases(text)

        # Record detection
        if biases:
            record = {
                "user_id": user_id,
                "text_preview": text[:100],
                "biases_detected": [b["bias"] for b in biases],
                "severity_max": max((b["severity"] for b in biases), key=lambda s: {"high": 3, "medium": 2, "low": 1}.get(s, 0)) if biases else "none",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._history.setdefault(user_id, []).append(record)
            self._persist(record)

        # Build warning message
        warnings = []
        for b in biases:
            warnings.append(f"[{b['severity'].upper()}] {b['bias']}: {b['suggestion']}")

        # Apply basic text corrections for backward compatibility
        cleaned = text
        cleaned = cleaned.replace("confio demasiado", "evaluo objetivamente")
        cleaned = cleaned.replace("confio demasiado", "evaluo objetivamente")

        return {
            "original_text": text,
            "cleaned_text": cleaned,
            "biases_detected": biases,
            "warnings": warnings,
            "bias_count": len(biases),
            "has_high_severity": any(b["severity"] == "high" for b in biases),
        }

    def get_bias_report(self, user_id: str) -> dict:
        """
        Generate a bias report for a user showing patterns over time.
        """
        records = self._history.get(user_id, [])
        if not records:
            return {
                "user_id": user_id,
                "total_scans": 0,
                "bias_frequency": {},
                "most_common_bias": None,
                "severity_distribution": {},
                "recommendations": ["No bias data available yet."],
            }

        # Count bias frequencies
        bias_freq: Dict[str, int] = {}
        severity_dist: Dict[str, int] = {"high": 0, "medium": 0, "low": 0}

        for rec in records:
            for bias_name in rec.get("biases_detected", []):
                bias_freq[bias_name] = bias_freq.get(bias_name, 0) + 1
            sev = rec.get("severity_max", "low")
            if sev in severity_dist:
                severity_dist[sev] += 1

        most_common = max(bias_freq, key=bias_freq.get) if bias_freq else None

        # Generate recommendations
        recommendations = []
        if most_common:
            info = BIAS_PATTERNS.get(most_common, {})
            recommendations.append(
                f"Your most common bias is '{most_common}': {info.get('description', '')} "
                f"Suggestion: {info.get('suggestion', '')}"
            )
        if severity_dist.get("high", 0) > 3:
            recommendations.append(
                "You have multiple high-severity bias detections. "
                "Consider implementing a mandatory cooling-off period before major decisions."
            )
        if not recommendations:
            recommendations.append("Your bias profile is within acceptable range.")

        return {
            "user_id": user_id,
            "total_scans": len(records),
            "bias_frequency": dict(sorted(bias_freq.items(), key=lambda x: x[1], reverse=True)),
            "most_common_bias": most_common,
            "severity_distribution": severity_dist,
            "recommendations": recommendations,
        }
