"""
Bruce AI -- Human Core Module

Makes Bruce feel human. Advanced emotion detection, sentiment analysis,
user adaptation, conversation memory, translation, empathy, and personality evolution.

All classes are importable individually. State persists to data/human_core/.
Thread-safe for async use.
"""

import json
import logging
import re
import threading
import unicodedata
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("Bruce.HumanCore")

DATA_DIR = Path("./data/human_core")
DATA_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Utilities
# =============================================================================

def _load_json(filename: str, default: Any = None) -> Any:
    """Load JSON from data/human_core/, returning *default* on any failure."""
    path = DATA_DIR / filename
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as exc:
            logger.warning("Failed to load %s: %s", filename, exc)
    return (default if default is not None else {}).copy() if isinstance(default, dict) else (default or [])


def _save_json(filename: str, data: Any) -> None:
    """Atomically save JSON to data/human_core/."""
    path = DATA_DIR / filename
    tmp = path.with_suffix(".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False, default=str)
        tmp.replace(path)
    except Exception as exc:
        logger.error("Failed to save %s: %s", filename, exc)
        if tmp.exists():
            tmp.unlink()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# =============================================================================
# 1. Advanced Emotion Detection
# =============================================================================

class EmotionDetector:
    """
    Detects emotions from text using multiple signals:
      - Keyword matching (200+ words across 12 emotions)
      - Punctuation analysis
      - Sentence structure
      - Emoji detection
    Tracks per-user emotion history and detects transitions.
    """

    EMOTIONS = [
        "joy", "sadness", "anger", "fear", "surprise", "disgust",
        "trust", "anticipation", "love", "anxiety", "frustration", "excitement",
    ]

    # 200+ keywords mapped to emotions
    KEYWORD_MAP: Dict[str, List[str]] = {
        "joy": [
            "happy", "glad", "cheerful", "delighted", "pleased", "elated", "thrilled",
            "joyful", "wonderful", "great", "awesome", "fantastic", "excellent", "amazing",
            "love it", "perfect", "brilliant", "superb", "magnificent",
            "feliz", "contento", "genial", "excelente", "maravilloso", "perfecto",
        ],
        "sadness": [
            "sad", "unhappy", "depressed", "miserable", "heartbroken", "grief", "sorrow",
            "melancholy", "gloomy", "down", "blue", "devastated", "hopeless", "lonely",
            "disappointed", "upset", "crying", "tears",
            "triste", "deprimido", "decepcionado", "desanimado",
        ],
        "anger": [
            "angry", "furious", "mad", "rage", "hate", "outraged", "livid", "infuriated",
            "pissed", "annoyed", "irritated", "enraged", "hostile", "bitter", "resentful",
            "disgusted", "fed up", "sick of",
            "enojado", "furioso", "odio", "rabia", "molesto",
        ],
        "fear": [
            "afraid", "scared", "terrified", "frightened", "horrified", "panicked",
            "alarmed", "dread", "phobia", "terror", "shaking", "nightmare", "creepy",
            "dangerous", "threat", "risk",
            "miedo", "asustado", "aterrorizado", "peligro",
        ],
        "surprise": [
            "surprised", "shocked", "amazed", "astonished", "stunned", "unexpected",
            "unbelievable", "incredible", "wow", "whoa", "omg", "no way", "really",
            "can't believe", "mind blown",
            "sorprendido", "impactado", "increible",
        ],
        "disgust": [
            "disgusting", "gross", "revolting", "repulsive", "nauseating", "vile",
            "horrible", "terrible", "awful", "dreadful", "nasty", "repugnant", "sickening",
            "asqueroso", "horrible", "repugnante",
        ],
        "trust": [
            "trust", "believe", "confident", "reliable", "dependable", "loyal", "faithful",
            "honest", "safe", "secure", "sure", "certain", "count on", "rely on",
            "confio", "seguro", "confiable", "leal",
        ],
        "anticipation": [
            "waiting", "expecting", "anticipate", "looking forward", "excited about",
            "can't wait", "eager", "hopeful", "soon", "ready", "prepared", "planning",
            "upcoming", "next",
            "esperando", "ansioso", "preparado", "listo",
        ],
        "love": [
            "love", "adore", "cherish", "devoted", "affection", "passion", "romantic",
            "darling", "sweetheart", "beloved", "heart", "soulmate", "caring", "tender",
            "warm", "embrace",
            "amor", "te quiero", "carino", "adorar",
        ],
        "anxiety": [
            "anxious", "worried", "nervous", "stressed", "uneasy", "tense", "restless",
            "overthinking", "panic", "overwhelmed", "pressure", "burden", "insomnia",
            "can't sleep", "freaking out", "on edge",
            "ansioso", "preocupado", "nervioso", "estresado",
        ],
        "frustration": [
            "frustrated", "stuck", "blocked", "impossible", "useless", "pointless",
            "waste", "broken", "doesn't work", "failed", "failing", "give up",
            "tired of", "enough", "ugh", "argh", "damn", "crap",
            "frustrado", "atascado", "imposible", "no funciona", "no sirve",
        ],
        "excitement": [
            "excited", "pumped", "stoked", "hyped", "thrilling", "electrifying",
            "adrenaline", "buzzing", "fired up", "let's go", "can't wait", "yay",
            "woohoo", "hell yeah", "amazing",
            "emocionado", "entusiasmado", "vamos",
        ],
    }

    # Emoji-to-emotion mapping
    EMOJI_EMOTIONS: Dict[str, str] = {
        # Joy / positive
        "\U0001f600": "joy", "\U0001f601": "joy", "\U0001f602": "joy",
        "\U0001f603": "joy", "\U0001f604": "joy", "\U0001f605": "joy",
        "\U0001f606": "joy", "\U0001f60a": "joy", "\U0001f60b": "joy",
        "\U0001f60d": "love", "\U0001f618": "love", "\U0001f970": "love",
        "\u2764": "love", "\U0001f496": "love", "\U0001f495": "love",
        # Sadness
        "\U0001f622": "sadness", "\U0001f625": "sadness", "\U0001f62d": "sadness",
        "\U0001f614": "sadness", "\U0001f61e": "sadness",
        # Anger
        "\U0001f620": "anger", "\U0001f621": "anger", "\U0001f624": "anger",
        "\U0001f92c": "anger",
        # Fear
        "\U0001f628": "fear", "\U0001f630": "fear", "\U0001f631": "fear",
        "\U0001f627": "fear",
        # Surprise
        "\U0001f632": "surprise", "\U0001f62e": "surprise", "\U0001f62f": "surprise",
        "\U0001f92f": "surprise",
        # Disgust
        "\U0001f922": "disgust", "\U0001f92e": "disgust",
        # Excitement
        "\U0001f389": "excitement", "\U0001f38a": "excitement", "\U0001f525": "excitement",
        "\U0001f680": "excitement", "\U0001f929": "excitement",
        # Anxiety
        "\U0001f630": "anxiety", "\U0001f613": "anxiety", "\U0001f615": "anxiety",
        # Frustration
        "\U0001f612": "frustration", "\U0001f624": "frustration", "\U0001f644": "frustration",
    }

    def __init__(self):
        self._lock = threading.Lock()
        self._history: Dict[str, List[Dict]] = _load_json("emotion_history.json", {})

    def detect(self, text: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Detect the dominant emotion from *text*.
        Returns dict with emotion, intensity (0-1), confidence, signals breakdown,
        and any transition from the user's previous emotion.
        """
        signals: Dict[str, float] = defaultdict(float)

        # --- Signal 1: Keyword matching ---
        text_lower = text.lower()
        for emotion, keywords in self.KEYWORD_MAP.items():
            for kw in keywords:
                if kw in text_lower:
                    signals[emotion] += 0.25

        # --- Signal 2: Punctuation analysis ---
        excl_count = text.count("!")
        quest_count = text.count("?")
        ellipsis_count = text.count("...")
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)

        if excl_count >= 3:
            signals["excitement"] += 0.3
            signals["anger"] += 0.15
        elif excl_count >= 1:
            signals["excitement"] += 0.1

        if quest_count >= 3:
            signals["anxiety"] += 0.2
            signals["surprise"] += 0.15
        elif quest_count >= 1:
            signals["anticipation"] += 0.05

        if ellipsis_count >= 2:
            signals["sadness"] += 0.15
            signals["anxiety"] += 0.1

        if caps_ratio > 0.5 and len(text) > 5:
            signals["anger"] += 0.3
            signals["excitement"] += 0.2

        # --- Signal 3: Sentence structure ---
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        avg_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

        if avg_len <= 3:
            signals["anger"] += 0.1
            signals["frustration"] += 0.1
        elif avg_len >= 15:
            signals["anticipation"] += 0.1
            signals["trust"] += 0.05

        # --- Signal 4: Emoji detection ---
        for char in text:
            emo = self.EMOJI_EMOTIONS.get(char)
            if emo:
                signals[emo] += 0.35

        # Two-char emoji sequences
        for i in range(len(text) - 1):
            pair = text[i:i+2]
            emo = self.EMOJI_EMOTIONS.get(pair)
            if emo:
                signals[emo] += 0.35

        # --- Determine dominant emotion ---
        if not signals:
            return {
                "emotion": "trust",
                "intensity": 0.3,
                "confidence": 0.2,
                "signals": {},
                "transition": None,
            }

        dominant = max(signals, key=signals.get)
        raw_intensity = min(1.0, signals[dominant])
        total_signal = sum(signals.values())
        confidence = min(0.95, raw_intensity / max(total_signal, 0.01) * 0.7 + 0.2)

        # --- Detect transition ---
        transition = None
        with self._lock:
            user_hist = self._history.setdefault(user_id, [])
            if user_hist:
                prev = user_hist[-1]["emotion"]
                if prev != dominant:
                    transition = {"from": prev, "to": dominant}

            user_hist.append({
                "emotion": dominant,
                "intensity": round(raw_intensity, 3),
                "confidence": round(confidence, 3),
                "timestamp": _now_iso(),
            })
            # Keep last 200 entries per user
            if len(user_hist) > 200:
                self._history[user_id] = user_hist[-200:]

            _save_json("emotion_history.json", self._history)

        return {
            "emotion": dominant,
            "intensity": round(raw_intensity, 3),
            "confidence": round(confidence, 3),
            "signals": {k: round(v, 3) for k, v in sorted(signals.items(), key=lambda x: -x[1])[:5]},
            "transition": transition,
        }

    def get_history(self, user_id: str = "default", last_n: int = 20) -> List[Dict]:
        with self._lock:
            return list(self._history.get(user_id, []))[-last_n:]

    def get_baseline(self, user_id: str = "default") -> Optional[str]:
        """Return the user's most frequent emotion (baseline mood)."""
        hist = self._history.get(user_id, [])
        if len(hist) < 5:
            return None
        counts: Dict[str, int] = defaultdict(int)
        for entry in hist[-50:]:
            counts[entry["emotion"]] += 1
        return max(counts, key=counts.get)


# =============================================================================
# 2. Sentiment Analysis
# =============================================================================

class SentimentAnalyzer:
    """
    Multi-dimensional sentiment: general polarity, financial sentiment,
    sarcasm hints, aggregate conversation sentiment, Fear & Greed index.
    """

    POSITIVE_WORDS = {
        "good", "great", "excellent", "amazing", "wonderful", "fantastic", "love",
        "happy", "perfect", "best", "brilliant", "awesome", "outstanding", "superb",
        "beautiful", "win", "profit", "gain", "success", "growth", "up", "moon",
        "bull", "bullish", "rally", "surge", "boom", "opportunity", "strong",
        "bueno", "genial", "excelente", "perfecto", "increible", "ganancia",
    }
    NEGATIVE_WORDS = {
        "bad", "terrible", "awful", "horrible", "hate", "worst", "ugly", "fail",
        "loss", "crash", "dump", "bear", "bearish", "decline", "drop", "fall",
        "fear", "panic", "recession", "crisis", "risk", "danger", "broke", "scam",
        "fraud", "waste", "useless", "stupid", "ruin", "collapse",
        "malo", "terrible", "horrible", "perdida", "caida", "crisis", "miedo",
    }
    FINANCIAL_BULLISH = {
        "bullish", "moon", "rally", "surge", "buy", "long", "breakout", "accumulate",
        "growth", "profit", "gain", "uptrend", "support", "golden cross", "undervalued",
    }
    FINANCIAL_BEARISH = {
        "bearish", "crash", "dump", "sell", "short", "breakdown", "distribution",
        "loss", "decline", "downtrend", "resistance", "death cross", "overvalued",
    }
    FINANCIAL_FEAR = {
        "fear", "panic", "scared", "crash", "collapse", "recession", "risk",
        "danger", "bubble", "liquidation", "margin call", "rug pull",
    }
    FINANCIAL_GREED = {
        "moon", "lambo", "100x", "easy money", "guaranteed", "all in",
        "fomo", "yolo", "to the moon", "diamond hands", "never sell",
    }
    SARCASM_MARKERS = {
        "oh great", "just wonderful", "how lovely", "yeah right", "sure thing",
        "oh fantastic", "what a surprise", "oh joy", "brilliant idea", "thanks a lot",
        "oh perfect", "just perfect", "absolutely wonderful",
    }

    def __init__(self):
        self._lock = threading.Lock()
        self._conversation_sentiments: Dict[str, List[Dict]] = {}

    def analyze(self, text: str, user_id: str = "default") -> Dict[str, Any]:
        """Full sentiment analysis on a single message."""
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))

        pos = len(words & self.POSITIVE_WORDS)
        neg = len(words & self.NEGATIVE_WORDS)
        total = pos + neg

        if total == 0:
            polarity = 0.0
        else:
            polarity = (pos - neg) / total  # -1..+1

        # Sarcasm detection
        sarcasm = any(marker in text_lower for marker in self.SARCASM_MARKERS)
        if sarcasm:
            polarity = -abs(polarity) * 0.5 if polarity >= 0 else polarity

        label = "positive" if polarity > 0.15 else ("negative" if polarity < -0.15 else "neutral")

        # Financial sentiment
        bull = len(words & self.FINANCIAL_BULLISH)
        bear = len(words & self.FINANCIAL_BEARISH)
        fear_w = len(words & self.FINANCIAL_FEAR)
        greed_w = len(words & self.FINANCIAL_GREED)

        if bull + bear == 0:
            fin_label = "neutral"
        elif bull > bear:
            fin_label = "bullish"
        elif bear > bull:
            fin_label = "bearish"
        else:
            fin_label = "uncertain"

        if fear_w > greed_w:
            fin_label = "fearful"
        elif greed_w > fear_w:
            fin_label = "greedy"

        # Fear & Greed score: -100 (extreme fear) .. +100 (extreme greed)
        fg_score = int(((greed_w - fear_w) / max(greed_w + fear_w, 1)) * 100)

        result = {
            "polarity": round(polarity, 3),
            "label": label,
            "sarcasm_detected": sarcasm,
            "financial": {
                "sentiment": fin_label,
                "bullish_signals": bull,
                "bearish_signals": bear,
                "fear_greed_score": fg_score,
            },
        }

        # Track conversation aggregate
        with self._lock:
            conv = self._conversation_sentiments.setdefault(user_id, [])
            conv.append({"polarity": polarity, "timestamp": _now_iso()})
            if len(conv) > 100:
                self._conversation_sentiments[user_id] = conv[-100:]

        return result

    def get_aggregate(self, user_id: str = "default", last_n: int = 10) -> Dict[str, Any]:
        """Aggregate sentiment over recent messages."""
        with self._lock:
            entries = list(self._conversation_sentiments.get(user_id, []))[-last_n:]
        if not entries:
            return {"avg_polarity": 0.0, "trend": "stable", "messages_analyzed": 0}

        polarities = [e["polarity"] for e in entries]
        avg = sum(polarities) / len(polarities)

        if len(polarities) >= 3:
            recent = sum(polarities[-3:]) / 3
            older = sum(polarities[:-3]) / max(len(polarities) - 3, 1)
            if recent - older > 0.2:
                trend = "improving"
            elif older - recent > 0.2:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "avg_polarity": round(avg, 3),
            "trend": trend,
            "messages_analyzed": len(entries),
        }

    def fear_greed_index(self, user_id: str = "default") -> Dict[str, Any]:
        """Compute a composite Fear & Greed index from recent conversation."""
        with self._lock:
            entries = list(self._conversation_sentiments.get(user_id, []))[-20:]
        if not entries:
            return {"score": 50, "label": "neutral"}

        avg_pol = sum(e["polarity"] for e in entries) / len(entries)
        score = int(50 + avg_pol * 50)  # 0..100
        score = max(0, min(100, score))

        if score <= 20:
            label = "extreme_fear"
        elif score <= 40:
            label = "fear"
        elif score <= 60:
            label = "neutral"
        elif score <= 80:
            label = "greed"
        else:
            label = "extreme_greed"

        return {"score": score, "label": label}


# =============================================================================
# 3. User Adaptation Engine
# =============================================================================

class UserAdaptationEngine:
    """
    Tracks user preferences over time and adapts Bruce's response style.
    Persists to data/human_core/user_profiles.json.
    """

    DEFAULT_PROFILE = {
        "communication_style": "balanced",   # formal / informal / balanced
        "verbosity": "balanced",             # concise / balanced / verbose
        "technicality": "balanced",          # simple / balanced / technical
        "preferred_language": "auto",
        "response_length_pref": "medium",    # short / medium / long
        "topics_of_interest": {},            # topic -> weight
        "time_patterns": {},                 # hour -> count
        "emotional_baseline": "neutral",
        "humor_appreciation": 0.5,           # 0..1
        "interaction_count": 0,
        "last_seen": None,
    }

    # Language detection keywords (top languages)
    LANGUAGE_HINTS: Dict[str, List[str]] = {
        "es": ["que", "como", "para", "esto", "quiero", "hola", "bueno", "gracias", "por favor", "donde", "cuando"],
        "en": ["the", "what", "how", "this", "want", "hello", "please", "where", "when", "thank", "could"],
        "fr": ["que", "comment", "pour", "ceci", "bonjour", "merci", "oui", "non", "avec", "dans", "tres"],
        "pt": ["que", "como", "para", "isso", "quero", "obrigado", "bom", "voce", "onde", "quando"],
        "de": ["was", "wie", "das", "ich", "bitte", "danke", "gut", "hallo", "nicht", "aber"],
        "it": ["che", "come", "per", "questo", "ciao", "grazie", "buono", "dove", "quando", "molto"],
        "zh": ["\u4f60\u597d", "\u8c22\u8c22", "\u662f", "\u4e0d", "\u6211", "\u4ec0\u4e48", "\u600e\u4e48", "\u8fd9"],
        "ja": ["\u3053\u3093\u306b\u3061\u306f", "\u3042\u308a\u304c\u3068\u3046", "\u306f\u3044", "\u3044\u3044\u3048", "\u4f55"],
        "ko": ["\uc548\ub155", "\uac10\uc0ac", "\ub124", "\uc544\ub2c8\uc694", "\ubb50"],
        "ar": ["\u0645\u0631\u062d\u0628\u0627", "\u0634\u0643\u0631\u0627", "\u0646\u0639\u0645", "\u0644\u0627", "\u0643\u064a\u0641"],
        "ru": ["\u043f\u0440\u0438\u0432\u0435\u0442", "\u0441\u043f\u0430\u0441\u0438\u0431\u043e", "\u0434\u0430", "\u043d\u0435\u0442", "\u043a\u0430\u043a", "\u0447\u0442\u043e"],
        "hi": ["\u0928\u092e\u0938\u094d\u0924\u0947", "\u0927\u0928\u094d\u092f\u0935\u093e\u0926", "\u0939\u093e\u0901", "\u0928\u0939\u0940\u0902", "\u0915\u094d\u092f\u093e"],
    }

    INFORMAL_MARKERS = {
        "lol", "haha", "lmao", "omg", "bruh", "nah", "yeah", "yep", "nope",
        "gonna", "wanna", "gotta", "btw", "tbh", "imo", "wtf", "jaja", "xd",
        "bro", "dude", "yo", "sup", "hey",
    }
    FORMAL_MARKERS = {
        "therefore", "furthermore", "consequently", "regarding", "pursuant",
        "hereby", "accordingly", "henceforth", "please note", "kindly",
        "dear", "respectfully", "sincerely",
    }

    def __init__(self):
        self._lock = threading.Lock()
        self._profiles: Dict[str, Dict] = _load_json("user_profiles.json", {})

    def _get_profile(self, user_id: str) -> Dict:
        if user_id not in self._profiles:
            self._profiles[user_id] = self.DEFAULT_PROFILE.copy()
            self._profiles[user_id]["topics_of_interest"] = {}
            self._profiles[user_id]["time_patterns"] = {}
        return self._profiles[user_id]

    def observe(self, text: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Observe a user message and update the profile.
        Returns the current adaptation instructions for response generation.
        """
        with self._lock:
            profile = self._get_profile(user_id)
            profile["interaction_count"] += 1
            profile["last_seen"] = _now_iso()

            text_lower = text.lower()
            words = set(re.findall(r'\b\w+\b', text_lower))

            # --- Communication style ---
            informal_hits = len(words & self.INFORMAL_MARKERS)
            formal_hits = len(words & self.FORMAL_MARKERS)
            if informal_hits > formal_hits + 1:
                profile["communication_style"] = "informal"
            elif formal_hits > informal_hits + 1:
                profile["communication_style"] = "formal"

            # --- Verbosity (from message length) ---
            word_count = len(text.split())
            if word_count <= 5:
                self._nudge(profile, "verbosity", "concise")
                self._nudge(profile, "response_length_pref", "short")
            elif word_count >= 40:
                self._nudge(profile, "verbosity", "verbose")
                self._nudge(profile, "response_length_pref", "long")

            # --- Language detection ---
            detected_lang = self._detect_language(text)
            if detected_lang:
                profile["preferred_language"] = detected_lang

            # --- Topics of interest ---
            topic_keywords = {
                "trading": ["trade", "trading", "position", "order", "strategy", "profit", "loss"],
                "crypto": ["bitcoin", "btc", "eth", "crypto", "defi", "token", "solana", "blockchain"],
                "shipping": ["shipping", "freight", "container", "vessel", "port", "route"],
                "ai": ["model", "llm", "neural", "agent", "learning", "training", "gpt"],
                "finance": ["stock", "bond", "market", "invest", "portfolio", "dividend"],
                "coding": ["code", "python", "api", "deploy", "docker", "build", "debug", "git"],
                "macro": ["inflation", "gdp", "fed", "rates", "economy", "fiscal"],
            }
            for topic, kws in topic_keywords.items():
                if any(kw in text_lower for kw in kws):
                    topics = profile["topics_of_interest"]
                    topics[topic] = topics.get(topic, 0) + 1

            # --- Time patterns ---
            hour = str(datetime.now().hour)
            tp = profile["time_patterns"]
            tp[hour] = tp.get(hour, 0) + 1

            # --- Technicality detection ---
            technical_words = {
                "algorithm", "api", "async", "backend", "binary", "cache", "compile",
                "database", "deploy", "docker", "endpoint", "frontend", "git", "hash",
                "http", "json", "kernel", "lambda", "middleware", "node", "orm",
                "pipeline", "query", "regex", "schema", "thread", "vector", "webhook",
            }
            if len(words & technical_words) >= 2:
                self._nudge(profile, "technicality", "technical")

            _save_json("user_profiles.json", self._profiles)

            return self.get_adaptation(user_id)

    def get_adaptation(self, user_id: str = "default") -> Dict[str, Any]:
        """Return current adaptation instructions for generating a response."""
        profile = self._get_profile(user_id)
        top_topics = sorted(profile.get("topics_of_interest", {}).items(), key=lambda x: -x[1])[:5]

        return {
            "style": profile["communication_style"],
            "verbosity": profile["verbosity"],
            "technicality": profile["technicality"],
            "language": profile["preferred_language"],
            "response_length": profile["response_length_pref"],
            "top_topics": [t[0] for t in top_topics],
            "humor_level": profile.get("humor_appreciation", 0.5),
            "interaction_count": profile["interaction_count"],
        }

    def get_profile(self, user_id: str = "default") -> Dict:
        """Return the full profile for a user."""
        with self._lock:
            return self._get_profile(user_id).copy()

    def update_humor(self, user_id: str, delta: float):
        """Adjust humor appreciation. +delta when user laughs, -delta when jokes fall flat."""
        with self._lock:
            profile = self._get_profile(user_id)
            profile["humor_appreciation"] = max(0.0, min(1.0, profile.get("humor_appreciation", 0.5) + delta))
            _save_json("user_profiles.json", self._profiles)

    def _detect_language(self, text: str) -> Optional[str]:
        """Heuristic language detection from keywords and Unicode script."""
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))

        scores: Dict[str, int] = defaultdict(int)
        for lang, hints in self.LANGUAGE_HINTS.items():
            for hint in hints:
                if hint in words or hint in text_lower:
                    scores[lang] += 1

        # Check CJK / Arabic / Cyrillic / Devanagari characters
        for char in text:
            try:
                name = unicodedata.name(char, "")
            except ValueError:
                continue
            if "CJK" in name:
                scores["zh"] += 2
            elif "HIRAGANA" in name or "KATAKANA" in name:
                scores["ja"] += 2
            elif "HANGUL" in name:
                scores["ko"] += 2
            elif "ARABIC" in name:
                scores["ar"] += 2
            elif "CYRILLIC" in name:
                scores["ru"] += 2
            elif "DEVANAGARI" in name:
                scores["hi"] += 2

        if not scores:
            return None
        best = max(scores, key=scores.get)
        if scores[best] >= 2:
            return best
        return None

    @staticmethod
    def _nudge(profile: Dict, key: str, toward: str):
        """Gradually shift a preference toward *toward* without snapping instantly."""
        # Simple: just set it. With more data we could do weighted rolling averages.
        profile[key] = toward


# =============================================================================
# 4. Conversation Memory & Context
# =============================================================================

class ConversationMemory:
    """
    Remembers key facts about users across sessions: name, role, company,
    interests, important dates, preferences, past decisions.
    Builds a growing 'user story'.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._memories: Dict[str, Dict] = _load_json("conversation_memory.json", {})

    def _get_mem(self, user_id: str) -> Dict:
        if user_id not in self._memories:
            self._memories[user_id] = {
                "facts": {},       # key -> value
                "dates": [],       # {date, description}
                "preferences": [], # free-text preferences
                "decisions": [],   # {decision, outcome, timestamp}
                "story": [],       # chronological story fragments
                "created": _now_iso(),
            }
        return self._memories[user_id]

    def remember_fact(self, user_id: str, key: str, value: str):
        """Store or update a fact (name, role, company, etc.)."""
        with self._lock:
            mem = self._get_mem(user_id)
            mem["facts"][key] = value
            _save_json("conversation_memory.json", self._memories)
            logger.debug("Remembered fact for %s: %s = %s", user_id, key, value)

    def remember_date(self, user_id: str, date: str, description: str):
        with self._lock:
            mem = self._get_mem(user_id)
            mem["dates"].append({"date": date, "description": description, "added": _now_iso()})
            mem["dates"] = mem["dates"][-50:]
            _save_json("conversation_memory.json", self._memories)

    def remember_preference(self, user_id: str, preference: str):
        with self._lock:
            mem = self._get_mem(user_id)
            if preference not in mem["preferences"]:
                mem["preferences"].append(preference)
                mem["preferences"] = mem["preferences"][-100:]
                _save_json("conversation_memory.json", self._memories)

    def remember_decision(self, user_id: str, decision: str, outcome: str = "pending"):
        with self._lock:
            mem = self._get_mem(user_id)
            mem["decisions"].append({
                "decision": decision,
                "outcome": outcome,
                "timestamp": _now_iso(),
            })
            mem["decisions"] = mem["decisions"][-100:]
            _save_json("conversation_memory.json", self._memories)

    def add_story_fragment(self, user_id: str, fragment: str):
        """Add a narrative fragment to the user's growing story."""
        with self._lock:
            mem = self._get_mem(user_id)
            mem["story"].append({"text": fragment, "timestamp": _now_iso()})
            mem["story"] = mem["story"][-200:]
            _save_json("conversation_memory.json", self._memories)

    def recall(self, user_id: str) -> Dict[str, Any]:
        """Recall everything known about a user."""
        with self._lock:
            mem = self._get_mem(user_id)
            return {
                "facts": dict(mem.get("facts", {})),
                "recent_dates": mem.get("dates", [])[-5:],
                "preferences": mem.get("preferences", [])[-10:],
                "recent_decisions": mem.get("decisions", [])[-5:],
                "story_length": len(mem.get("story", [])),
            }

    def get_story_summary(self, user_id: str, last_n: int = 10) -> str:
        """Return a short narrative from the user's story."""
        with self._lock:
            mem = self._get_mem(user_id)
            fragments = mem.get("story", [])[-last_n:]
        if not fragments:
            return ""
        return " ".join(f["text"] for f in fragments)

    def extract_facts_from_text(self, text: str, user_id: str):
        """
        Heuristic fact extraction from user messages.
        Looks for patterns like 'my name is X', 'I work at Y', 'I prefer Z'.
        """
        text_lower = text.lower()

        # Name patterns
        for pattern in [r"(?:my name is|i'm|i am|me llamo|soy)\s+([A-Z][a-z]+)",
                        r"(?:call me)\s+([A-Z][a-z]+)"]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                self.remember_fact(user_id, "name", m.group(1))

        # Company
        for pattern in [r"(?:i work at|i'm at|work for|trabajo en)\s+(.+?)(?:\.|,|$)"]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                self.remember_fact(user_id, "company", m.group(1).strip())

        # Role
        for pattern in [r"(?:i'm a|i am a|i work as|soy)\s+(.+?)(?:\.|,|$)"]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                if len(val.split()) <= 5:
                    self.remember_fact(user_id, "role", val)

        # Preferences
        for pattern in [r"(?:i prefer|i like|prefiero|me gusta)\s+(.+?)(?:\.|,|!|$)"]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                self.remember_preference(user_id, m.group(1).strip())


# =============================================================================
# 5. Translation Engine
# =============================================================================

class TranslationEngine:
    """
    Detects input language and translates via LLM.
    Supports: en, es, fr, pt, de, it, zh, ja, ko, ar, ru, hi.
    """

    LANGUAGE_NAMES = {
        "en": "English", "es": "Spanish", "fr": "French", "pt": "Portuguese",
        "de": "German", "it": "Italian", "zh": "Chinese", "ja": "Japanese",
        "ko": "Korean", "ar": "Arabic", "ru": "Russian", "hi": "Hindi",
    }

    def __init__(self, llm_fn=None):
        self._llm_fn = llm_fn
        self._adaptation = UserAdaptationEngine()

    def set_llm(self, llm_fn):
        self._llm_fn = llm_fn

    def detect_language(self, text: str) -> str:
        """Detect the language of *text*. Returns ISO 639-1 code or 'en' as default."""
        detected = self._adaptation._detect_language(text)
        return detected or "en"

    def translate(self, text: str, target: str = "en", source: str = None) -> str:
        """
        Translate *text* to *target* language using the LLM.
        If no LLM is available, returns the original text.
        """
        if not self._llm_fn:
            logger.warning("Translation requested but no LLM available.")
            return text

        source_name = self.LANGUAGE_NAMES.get(source, "auto-detect")
        target_name = self.LANGUAGE_NAMES.get(target, target)

        prompt = (
            f"Translate the following text to {target_name}. "
            f"Return ONLY the translation, nothing else.\n\n"
            f"Text: {text}"
        )

        try:
            result = self._llm_fn(prompt)
            return result.strip() if result else text
        except Exception as exc:
            logger.error("Translation failed: %s", exc)
            return text

    def should_respond_in(self, user_text: str, user_id: str = "default") -> str:
        """Determine what language Bruce should respond in."""
        detected = self.detect_language(user_text)
        return detected


# =============================================================================
# 6. Empathy Engine
# =============================================================================

class EmpathyEngine:
    """
    Generates empathetic response prefixes and calibrates warmth
    based on detected emotion and relationship depth.
    """

    # Empathy templates per emotion
    RESPONSES: Dict[str, List[str]] = {
        "frustration": [
            "I hear you -- that sounds really frustrating. ",
            "I understand the frustration. Let me help sort this out. ",
            "That does sound annoying. Let's see what we can do. ",
        ],
        "anger": [
            "I can see this is upsetting. Let's work through it together. ",
            "I understand you're frustrated. Let me help. ",
        ],
        "sadness": [
            "I'm sorry to hear that. ",
            "That's tough. I'm here if you need anything. ",
            "I understand. Let's take it one step at a time. ",
        ],
        "fear": [
            "I understand the concern. Let me give you the facts. ",
            "It's normal to feel cautious here. Let me break it down. ",
        ],
        "anxiety": [
            "I get it -- there's a lot of uncertainty. Let me help clarify. ",
            "Take a breath. Let's look at this calmly together. ",
            "I understand the worry. Here's what I can tell you. ",
        ],
        "joy": [
            "That's great to hear! ",
            "Awesome! ",
            "Love that! ",
        ],
        "excitement": [
            "That's exciting! ",
            "I can feel the energy! ",
            "Let's ride this wave! ",
        ],
        "love": [
            "That's wonderful! ",
            "Beautiful. ",
        ],
        "surprise": [
            "Wow, that is unexpected! ",
            "Interesting development! ",
        ],
        "trust": [
            "",  # Trust needs no special prefix
        ],
        "anticipation": [
            "Looking forward to it too! ",
        ],
        "disgust": [
            "I can see why that's off-putting. ",
        ],
    }

    # Spanish variants
    RESPONSES_ES: Dict[str, List[str]] = {
        "frustration": [
            "Entiendo la frustracion. Veamos como resolver esto. ",
            "Te escucho -- eso suena frustrante. Dejame ayudar. ",
        ],
        "anger": [
            "Entiendo que estas molesto. Vamos a resolverlo juntos. ",
        ],
        "sadness": [
            "Lamento escuchar eso. Estoy aqui para ayudarte. ",
        ],
        "fear": [
            "Entiendo la preocupacion. Dejame darte los datos. ",
        ],
        "anxiety": [
            "Tranquilo. Vamos a analizar esto con calma. ",
        ],
        "joy": [
            "Que bueno! ",
            "Excelente! ",
        ],
        "excitement": [
            "Que emocion! ",
        ],
    }

    def __init__(self):
        self._interaction_counts: Dict[str, int] = {}

    def generate_empathy(self, emotion: str, intensity: float,
                         language: str = "en", user_id: str = "default") -> str:
        """
        Generate an empathetic prefix based on detected emotion and intensity.
        Higher intensity = stronger empathy.
        """
        if intensity < 0.2:
            return ""

        # Pick language-appropriate templates
        if language == "es":
            templates = self.RESPONSES_ES.get(emotion, self.RESPONSES.get(emotion, [""]))
        else:
            templates = self.RESPONSES.get(emotion, [""])

        if not templates or not templates[0]:
            return ""

        # Warmer responses for deeper relationships
        count = self._interaction_counts.get(user_id, 0)
        self._interaction_counts[user_id] = count + 1

        # Use higher-index (warmer) templates for more interactions
        warmth_idx = min(len(templates) - 1, count // 20)
        # But also vary it for naturalness
        import random
        idx = min(random.randint(0, warmth_idx + 1), len(templates) - 1)

        return templates[idx]

    def get_warmth_level(self, user_id: str = "default") -> str:
        """Return the relationship warmth level."""
        count = self._interaction_counts.get(user_id, 0)
        if count < 10:
            return "professional"
        elif count < 50:
            return "friendly"
        elif count < 200:
            return "warm"
        else:
            return "close"


# =============================================================================
# 7. Personality Evolution
# =============================================================================

class PersonalityEvolution:
    """
    Bruce's personality evolves based on interactions.
    Humor, formality, technical depth, and risk communication style all adapt.
    State persists to disk.
    """

    DEFAULT_STATE = {
        "humor": 0.3,          # 0..1
        "formality": 0.5,      # 0 = very informal, 1 = very formal
        "technical_depth": 0.5, # 0 = simple, 1 = deep
        "warmth": 0.5,         # 0 = cold/professional, 1 = warm/personal
        "risk_style": "balanced",  # conservative / balanced / aggressive
        "creativity": 0.5,     # 0 = factual, 1 = creative
        "proactivity": 0.5,    # 0 = reactive, 1 = proactive
        "evolution_log": [],
    }

    def __init__(self):
        self._lock = threading.Lock()
        self._state: Dict = _load_json("personality_state.json", self.DEFAULT_STATE.copy())
        # Ensure all keys exist
        for k, v in self.DEFAULT_STATE.items():
            if k not in self._state:
                self._state[k] = v

    @property
    def state(self) -> Dict:
        return {k: v for k, v in self._state.items() if k != "evolution_log"}

    def evolve(self, signal: str, value: float = 0.05):
        """
        Nudge personality based on a signal.
        Signals: 'humor_up', 'humor_down', 'more_formal', 'less_formal',
                 'more_technical', 'less_technical', 'warmer', 'colder',
                 'more_creative', 'less_creative', 'more_proactive', 'less_proactive'.
        """
        mapping = {
            "humor_up": ("humor", value),
            "humor_down": ("humor", -value),
            "more_formal": ("formality", value),
            "less_formal": ("formality", -value),
            "more_technical": ("technical_depth", value),
            "less_technical": ("technical_depth", -value),
            "warmer": ("warmth", value),
            "colder": ("warmth", -value),
            "more_creative": ("creativity", value),
            "less_creative": ("creativity", -value),
            "more_proactive": ("proactivity", value),
            "less_proactive": ("proactivity", -value),
        }

        if signal not in mapping:
            return

        key, delta = mapping[signal]
        with self._lock:
            old = self._state[key]
            self._state[key] = max(0.0, min(1.0, old + delta))
            self._state["evolution_log"].append({
                "signal": signal,
                "key": key,
                "old": round(old, 3),
                "new": round(self._state[key], 3),
                "timestamp": _now_iso(),
            })
            # Keep log manageable
            if len(self._state["evolution_log"]) > 500:
                self._state["evolution_log"] = self._state["evolution_log"][-500:]
            _save_json("personality_state.json", self._state)

        logger.debug("Personality evolved: %s %.3f -> %.3f", key, old, self._state[key])

    def adapt_from_user(self, adaptation: Dict[str, Any]):
        """Adapt personality dimensions from the UserAdaptationEngine output."""
        style = adaptation.get("style", "balanced")
        if style == "informal":
            self.evolve("less_formal", 0.02)
        elif style == "formal":
            self.evolve("more_formal", 0.02)

        tech = adaptation.get("technicality", "balanced")
        if tech == "technical":
            self.evolve("more_technical", 0.02)
        elif tech == "simple":
            self.evolve("less_technical", 0.02)

        humor = adaptation.get("humor_level", 0.5)
        if humor > 0.6:
            self.evolve("humor_up", 0.01)
        elif humor < 0.3:
            self.evolve("humor_down", 0.01)

    def set_risk_style(self, style: str):
        """Set risk communication style: conservative, balanced, aggressive."""
        if style in ("conservative", "balanced", "aggressive"):
            with self._lock:
                self._state["risk_style"] = style
                _save_json("personality_state.json", self._state)

    def get_prompt_modifiers(self) -> str:
        """Return personality modifiers as a string for LLM system prompts."""
        s = self._state
        parts = []

        if s["humor"] > 0.6:
            parts.append("Use occasional humor and wit.")
        elif s["humor"] < 0.2:
            parts.append("Keep responses serious and professional.")

        if s["formality"] > 0.7:
            parts.append("Use formal language.")
        elif s["formality"] < 0.3:
            parts.append("Use casual, conversational language.")

        if s["technical_depth"] > 0.7:
            parts.append("Provide detailed technical explanations.")
        elif s["technical_depth"] < 0.3:
            parts.append("Keep explanations simple and non-technical.")

        if s["warmth"] > 0.7:
            parts.append("Be warm and personable.")
        elif s["warmth"] < 0.3:
            parts.append("Be concise and direct.")

        if s["creativity"] > 0.7:
            parts.append("Be creative and offer novel perspectives.")

        return " ".join(parts) if parts else ""

    def get_evolution_summary(self) -> Dict:
        """Summary of personality evolution."""
        log = self._state.get("evolution_log", [])
        return {
            "current_state": self.state,
            "total_evolutions": len(log),
            "recent_changes": log[-10:] if log else [],
        }


# =============================================================================
# Unified Facade -- HumanCore
# =============================================================================

class HumanCore:
    """
    Unified facade that coordinates all human-like subsystems.
    Use this as the single entry point from bruce_agent.py.
    """

    def __init__(self, llm_fn=None):
        self.emotion_detector = EmotionDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.user_adaptation = UserAdaptationEngine()
        self.conversation_memory = ConversationMemory()
        self.translation = TranslationEngine(llm_fn=llm_fn)
        self.empathy = EmpathyEngine()
        self.personality = PersonalityEvolution()
        self._llm_fn = llm_fn
        logger.info("HumanCore initialized -- all subsystems online.")

    def set_llm(self, llm_fn):
        """Update the LLM function for translation and other LLM-dependent features."""
        self._llm_fn = llm_fn
        self.translation.set_llm(llm_fn)

    def process_input(self, text: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Process a user message through all human-core subsystems.
        Returns a dict with emotion, sentiment, adaptation, empathy prefix,
        detected language, and personality modifiers.

        Call this BEFORE generating a response.
        """
        # 1. Detect emotion
        emotion = self.emotion_detector.detect(text, user_id)

        # 2. Analyze sentiment
        sentiment = self.sentiment_analyzer.analyze(text, user_id)

        # 3. Observe user for adaptation
        adaptation = self.user_adaptation.observe(text, user_id)

        # 4. Extract facts for memory
        self.conversation_memory.extract_facts_from_text(text, user_id)

        # 5. Detect language
        language = adaptation.get("language", "en") or "en"
        if language == "auto":
            language = self.translation.detect_language(text)

        # 6. Generate empathy prefix
        empathy_prefix = self.empathy.generate_empathy(
            emotion["emotion"],
            emotion["intensity"],
            language=language,
            user_id=user_id,
        )

        # 7. Evolve personality based on user adaptation
        self.personality.adapt_from_user(adaptation)

        # 8. Get personality modifiers for prompting
        personality_mods = self.personality.get_prompt_modifiers()

        return {
            "emotion": emotion,
            "sentiment": sentiment,
            "adaptation": adaptation,
            "language": language,
            "empathy_prefix": empathy_prefix,
            "personality_modifiers": personality_mods,
            "warmth_level": self.empathy.get_warmth_level(user_id),
        }

    def build_prompt_context(self, human_input: Dict[str, Any], user_id: str = "default") -> str:
        """
        Build a context block for the LLM prompt from the process_input result.
        """
        parts = []

        emo = human_input["emotion"]
        parts.append(f"[User emotion: {emo['emotion']} (intensity: {emo['intensity']:.1f})]")

        if emo.get("transition"):
            t = emo["transition"]
            parts.append(f"[Emotion shift: {t['from']} -> {t['to']}]")

        sent = human_input["sentiment"]
        parts.append(f"[Sentiment: {sent['label']} (polarity: {sent['polarity']:.2f})]")
        if sent.get("sarcasm_detected"):
            parts.append("[Sarcasm detected -- user may be expressing the opposite of their words]")

        fin = sent.get("financial", {})
        if fin.get("sentiment") not in (None, "neutral"):
            parts.append(f"[Financial sentiment: {fin['sentiment']}]")

        adapt = human_input["adaptation"]
        parts.append(f"[Respond in: {human_input['language']}]")
        if adapt.get("style") != "balanced":
            parts.append(f"[User communication style: {adapt['style']}]")
        if adapt.get("verbosity") != "balanced":
            parts.append(f"[User prefers {adapt['verbosity']} responses]")

        # Recall memory
        memory = self.conversation_memory.recall(user_id)
        if memory.get("facts"):
            facts_str = ", ".join(f"{k}: {v}" for k, v in list(memory["facts"].items())[:5])
            parts.append(f"[Known about user: {facts_str}]")
        if memory.get("preferences"):
            prefs = "; ".join(memory["preferences"][-3:])
            parts.append(f"[User preferences: {prefs}]")

        mods = human_input.get("personality_modifiers", "")
        if mods:
            parts.append(f"[Personality: {mods}]")

        return "\n".join(parts)

    def post_response(self, user_text: str, response: str, user_id: str = "default"):
        """
        Call AFTER generating a response to update memory and track story.
        """
        # Add to story
        summary = user_text[:80]
        self.conversation_memory.add_story_fragment(
            user_id,
            f"User said: '{summary}' -- Bruce responded."
        )

        # Detect humor appreciation signals
        humor_signals = ["haha", "lol", "lmao", "jaja", "xd", "funny"]
        if any(s in user_text.lower() for s in humor_signals):
            self.user_adaptation.update_humor(user_id, 0.05)
            self.personality.evolve("humor_up", 0.02)

    def translate(self, text: str, target: str = "en", source: str = None) -> str:
        """Explicit translation interface."""
        return self.translation.translate(text, target=target, source=source)

    def get_user_summary(self, user_id: str = "default") -> Dict[str, Any]:
        """Get a full summary of everything known about a user."""
        return {
            "memory": self.conversation_memory.recall(user_id),
            "profile": self.user_adaptation.get_profile(user_id),
            "emotion_baseline": self.emotion_detector.get_baseline(user_id),
            "emotion_history": self.emotion_detector.get_history(user_id, last_n=10),
            "sentiment_aggregate": self.sentiment_analyzer.get_aggregate(user_id),
            "fear_greed": self.sentiment_analyzer.fear_greed_index(user_id),
            "warmth_level": self.empathy.get_warmth_level(user_id),
            "personality": self.personality.state,
        }


# =============================================================================
# Module-level convenience
# =============================================================================

_instance: Optional[HumanCore] = None
_instance_lock = threading.Lock()


def get_human_core(llm_fn=None) -> HumanCore:
    """Get or create the singleton HumanCore instance."""
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = HumanCore(llm_fn=llm_fn)
        elif llm_fn is not None and _instance._llm_fn is None:
            _instance.set_llm(llm_fn)
    return _instance
