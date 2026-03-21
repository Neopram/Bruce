
# narrador.py
"""
Cognitive Explanation and Counterfactual Thinking Module.
Generates narratives about market state, explains past decisions,
simulates alternative scenarios, and provides configurable narration styles.
"""

from datetime import datetime, timezone
import random
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("Bruce.Narrador")
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
#  Narration style templates
# ---------------------------------------------------------------------------

NARRATION_STYLES = {
    "formal": {
        "description": "Professional, data-driven narration.",
        "operation_template": (
            "On {fecha}, an operation was executed using the {modelo} model. "
            "The primary rationale was: {razon}. The outcome recorded was: {resultado}."
        ),
        "counterfactual_template": (
            "Had the decision been '{alternativa}' instead of '{decision}', "
            "the projected outcome would have been approximately {resultado_alt}%."
        ),
        "market_intro": "Market Summary Report:",
        "trend_up": "The market exhibits upward momentum with sustained buying pressure.",
        "trend_down": "The market is experiencing a correction with notable selling activity.",
        "trend_sideways": "The market is consolidating within a defined range.",
        "separator": " | ",
    },
    "casual": {
        "description": "Friendly, accessible narration.",
        "operation_template": (
            "So on {fecha}, we ran a trade using {modelo}. "
            "The thinking was: {razon}. And the result? {resultado}."
        ),
        "counterfactual_template": (
            "What if we had gone with '{alternativa}' instead of '{decision}'? "
            "We'd probably be looking at around {resultado_alt}%."
        ),
        "market_intro": "Here's what's going on in the market:",
        "trend_up": "Things are looking up - buyers are in control right now.",
        "trend_down": "It's getting a bit rough out there - sellers are pushing prices down.",
        "trend_sideways": "Not much action - we're stuck in a range for now.",
        "separator": " - ",
    },
    "dramatic": {
        "description": "Vivid, storytelling-style narration.",
        "operation_template": (
            "The date was {fecha}. Armed with the {modelo} model, a bold move was made. "
            "The conviction: {razon}. The verdict of the market: {resultado}."
        ),
        "counterfactual_template": (
            "In an alternate timeline where '{alternativa}' was chosen over '{decision}', "
            "fortune would have smiled (or frowned) to the tune of {resultado_alt}%."
        ),
        "market_intro": "The Arena of Markets speaks:",
        "trend_up": "The bulls charge forward with thundering hooves, carrying prices ever higher!",
        "trend_down": "A storm brews in the markets. The bears have awakened from their slumber.",
        "trend_sideways": "An uneasy calm settles over the battlefield. Both sides gather strength.",
        "separator": " ~ ",
    },
}

DEFAULT_STYLE = "formal"


# ---------------------------------------------------------------------------
#  Original functions (preserved and expanded)
# ---------------------------------------------------------------------------

def explicar_operacion(operacion: dict, style: str = DEFAULT_STYLE) -> str:
    """
    Explain a past operation/trade in the chosen narration style.
    """
    s = NARRATION_STYLES.get(style, NARRATION_STYLES[DEFAULT_STYLE])

    razon = operacion.get("razon", "Not specified")
    modelo = operacion.get("modelo", "Unknown")
    resultado = operacion.get("resultado", "no result recorded")
    fecha = operacion.get("fecha", datetime.now(timezone.utc).isoformat())

    return s["operation_template"].format(
        fecha=fecha, modelo=modelo, razon=razon, resultado=resultado
    )


def contrafactual(operacion: dict, style: str = DEFAULT_STYLE) -> str:
    """
    Generate a counterfactual scenario for a past operation.
    """
    s = NARRATION_STYLES.get(style, NARRATION_STYLES[DEFAULT_STYLE])

    resultado_alternativo = round(random.uniform(-3.0, 5.0), 2)
    decision = operacion.get("decision", "the action taken")
    decision_alternativa = operacion.get("alternativa", "wait")

    return s["counterfactual_template"].format(
        alternativa=decision_alternativa,
        decision=decision,
        resultado_alt=resultado_alternativo,
    )


# ---------------------------------------------------------------------------
#  Narrator class for richer narration capabilities
# ---------------------------------------------------------------------------

class Narrator:
    """
    Generates narratives about market state, decisions, and system behavior.
    Configurable style and integrated TTS-ready output.
    """

    def __init__(self, style: str = DEFAULT_STYLE):
        self.style = style if style in NARRATION_STYLES else DEFAULT_STYLE
        self._narration_history: List[dict] = []

    def set_style(self, style: str):
        """Change the narration style."""
        if style in NARRATION_STYLES:
            self.style = style
            logger.info(f"[Narrator] Style changed to: {style}")
        else:
            logger.warning(f"[Narrator] Unknown style '{style}', keeping '{self.style}'")

    def get_available_styles(self) -> Dict[str, str]:
        """Return available narration styles and their descriptions."""
        return {name: s["description"] for name, s in NARRATION_STYLES.items()}

    def narrate_operation(self, operacion: dict) -> str:
        """Narrate a single operation."""
        text = explicar_operacion(operacion, self.style)
        self._record("operation", text)
        return text

    def narrate_counterfactual(self, operacion: dict) -> str:
        """Narrate a counterfactual scenario."""
        text = contrafactual(operacion, self.style)
        self._record("counterfactual", text)
        return text

    def narrate_market_state(
        self,
        symbol: str = "BTC",
        price: Optional[float] = None,
        change_24h: Optional[float] = None,
        volume: Optional[float] = None,
        trend: str = "sideways",
        extra_context: Optional[str] = None,
    ) -> str:
        """
        Generate a narrative summary of the current market state.
        """
        s = NARRATION_STYLES.get(self.style, NARRATION_STYLES[DEFAULT_STYLE])
        sep = s["separator"]

        parts = [s["market_intro"]]

        # Price info
        if price is not None:
            parts.append(f"{symbol}: ${price:,.2f}")

        # 24h change
        if change_24h is not None:
            direction = "up" if change_24h >= 0 else "down"
            parts.append(f"24h change: {change_24h:+.2f}% ({direction})")

        # Volume
        if volume is not None:
            if volume >= 1_000_000_000:
                vol_str = f"${volume / 1_000_000_000:.1f}B"
            elif volume >= 1_000_000:
                vol_str = f"${volume / 1_000_000:.1f}M"
            else:
                vol_str = f"${volume:,.0f}"
            parts.append(f"Volume: {vol_str}")

        # Trend narration
        trend_key = f"trend_{trend}" if f"trend_{trend}" in s else "trend_sideways"
        parts.append(s.get(trend_key, s["trend_sideways"]))

        # Extra context
        if extra_context:
            parts.append(extra_context)

        narrative = sep.join(parts)
        self._record("market_state", narrative)
        return narrative

    def narrate_market_summary(
        self,
        assets: List[dict],
        macro_outlook: Optional[str] = None,
    ) -> str:
        """
        Generate a multi-asset market summary narrative.
        Each asset dict should contain: symbol, price, change_24h, trend.
        """
        s = NARRATION_STYLES.get(self.style, NARRATION_STYLES[DEFAULT_STYLE])
        lines = [s["market_intro"], ""]

        for asset in assets:
            symbol = asset.get("symbol", "???")
            price = asset.get("price")
            change = asset.get("change_24h")
            trend = asset.get("trend", "sideways")

            line_parts = [f"  {symbol}:"]
            if price is not None:
                line_parts.append(f"${price:,.2f}")
            if change is not None:
                line_parts.append(f"({change:+.2f}%)")

            trend_key = f"trend_{trend}"
            trend_text = s.get(trend_key, "")
            if trend_text:
                line_parts.append(f"- {trend_text}")

            lines.append(" ".join(line_parts))

        if macro_outlook:
            lines.append("")
            lines.append(f"Macro outlook: {macro_outlook}")

        narrative = "\n".join(lines)
        self._record("market_summary", narrative)
        return narrative

    def prepare_for_tts(self, text: str) -> dict:
        """
        Prepare narration text for text-to-speech integration.
        Returns structured data with the text and recommended TTS parameters.
        """
        # Estimate speaking time (~150 words per minute)
        word_count = len(text.split())
        estimated_seconds = round(word_count / 2.5, 1)

        tts_config = {
            "formal": {"voice": "en-US-Neural-D", "speed": 1.0, "pitch": 0.0},
            "casual": {"voice": "en-US-Neural-J", "speed": 1.05, "pitch": 0.5},
            "dramatic": {"voice": "en-US-Neural-A", "speed": 0.9, "pitch": -1.0},
        }

        config = tts_config.get(self.style, tts_config["formal"])

        return {
            "text": text,
            "word_count": word_count,
            "estimated_duration_seconds": estimated_seconds,
            "tts_config": config,
            "style": self.style,
        }

    def _record(self, narration_type: str, text: str):
        """Record narration in history."""
        self._narration_history.append({
            "type": narration_type,
            "style": self.style,
            "text": text[:200],  # preview only
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # Keep history bounded
        if len(self._narration_history) > 100:
            self._narration_history = self._narration_history[-100:]

    def get_history(self, limit: int = 10) -> List[dict]:
        """Return recent narration history."""
        return self._narration_history[-limit:]
