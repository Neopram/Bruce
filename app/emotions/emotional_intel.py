# Emotion detection model to guide trading behavior
import re


class EmotionalIntel:
    """Emotional intelligence module for sentiment analysis and empathetic responses."""

    POSITIVE_WORDS = {
        "good", "great", "excellent", "amazing", "wonderful", "happy", "excited",
        "bullish", "profit", "gain", "win", "up", "moon", "rally", "surge",
        "confident", "optimistic", "love", "fantastic", "awesome", "brilliant",
    }
    NEGATIVE_WORDS = {
        "bad", "terrible", "awful", "horrible", "sad", "angry", "frustrated",
        "bearish", "loss", "crash", "down", "dump", "fear", "panic", "worry",
        "stressed", "anxious", "hate", "worst", "painful", "devastated",
    }
    EMOTION_PATTERNS = {
        "joy": ["happy", "excited", "great", "amazing", "love", "wonderful", "profit", "moon"],
        "fear": ["afraid", "scared", "worry", "panic", "fear", "crash", "dump", "loss"],
        "anger": ["angry", "furious", "mad", "hate", "frustrated", "annoyed", "outraged"],
        "sadness": ["sad", "depressed", "down", "miserable", "heartbroken", "devastated"],
        "surprise": ["shocked", "surprised", "unexpected", "wow", "unbelievable", "sudden"],
        "trust": ["confident", "trust", "reliable", "solid", "safe", "secure", "bullish"],
    }

    EMPATHY_TEMPLATES = {
        "joy": [
            "That's wonderful to hear! Let's keep this momentum going.",
            "Great energy! This positive outlook can inform sound decisions.",
        ],
        "fear": [
            "I understand your concern. Let's look at the data objectively.",
            "Market uncertainty is natural. Let me help you assess the risk calmly.",
        ],
        "anger": [
            "I hear your frustration. Let's take a step back and review the situation.",
            "That's understandable. Let me help you channel that into a clear plan.",
        ],
        "sadness": [
            "I'm sorry you're going through this. Markets have cycles - let's review your options.",
            "Losses are tough. Let's focus on what we can control going forward.",
        ],
        "surprise": [
            "That is unexpected! Let's analyze what this means for your positions.",
            "Sudden moves require careful assessment. Let me help you process this.",
        ],
        "trust": [
            "Your confidence is noted. Let's make sure the fundamentals support it.",
            "Solid conviction. Let me provide the data to back up your thesis.",
        ],
    }

    def analyze_sentiment(self, text):
        """Analyze sentiment of text, returning score from -1 (negative) to 1 (positive).

        Args:
            text: Input text to analyze.

        Returns:
            Dict with score, label, and word counts.
        """
        words = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
        pos_matches = words & self.POSITIVE_WORDS
        neg_matches = words & self.NEGATIVE_WORDS

        pos_count = len(pos_matches)
        neg_count = len(neg_matches)
        total = pos_count + neg_count

        if total == 0:
            score = 0.0
            label = "neutral"
        else:
            score = round((pos_count - neg_count) / total, 3)
            if score > 0.2:
                label = "positive"
            elif score < -0.2:
                label = "negative"
            else:
                label = "neutral"

        return {
            "score": score,
            "label": label,
            "positive_words": list(pos_matches),
            "negative_words": list(neg_matches),
        }

    def detect_emotion(self, text):
        """Detect the dominant emotion in text.

        Args:
            text: Input text to analyze.

        Returns:
            Dict with dominant emotion, confidence, and all emotion scores.
        """
        text_lower = text.lower()
        scores = {}

        for emotion, keywords in self.EMOTION_PATTERNS.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            scores[emotion] = matches

        total = sum(scores.values())
        if total == 0:
            return {"dominant_emotion": "neutral", "confidence": 0.0, "scores": scores}

        normalized = {e: round(s / total, 3) for e, s in scores.items()}
        dominant = max(scores, key=scores.get)
        confidence = round(scores[dominant] / total, 3)

        return {
            "dominant_emotion": dominant,
            "confidence": confidence,
            "scores": normalized,
        }

    def get_empathy_response(self, emotion, context=None):
        """Generate an empathetic response suggestion based on detected emotion.

        Args:
            emotion: Emotion string (e.g., 'fear', 'joy').
            context: Optional context dict with additional information.

        Returns:
            Dict with suggested response and guidance.
        """
        templates = self.EMPATHY_TEMPLATES.get(emotion, [
            "I understand. Let me help you think through this clearly.",
        ])

        import random
        response = random.choice(templates)

        if context and context.get("portfolio_change"):
            change = context["portfolio_change"]
            if change < -0.05:
                response += " Your portfolio has seen a notable decline - let's review risk management."
            elif change > 0.1:
                response += " Your portfolio is performing well - consider reviewing your take-profit levels."

        return {
            "emotion": emotion,
            "response": response,
            "recommended_action": self._get_recommended_action(emotion),
        }

    def assess_emotional_state(self, history):
        """Assess overall emotional state from a history of interactions.

        Args:
            history: List of text strings from recent interactions.

        Returns:
            Dict with overall state, trend, and recommendation.
        """
        if not history:
            return {"state": "unknown", "trend": "stable", "recommendation": "No data available"}

        sentiments = [self.analyze_sentiment(text)["score"] for text in history]
        emotions = [self.detect_emotion(text)["dominant_emotion"] for text in history]

        avg_sentiment = round(sum(sentiments) / len(sentiments), 3)

        # Detect trend from recent vs older sentiment
        mid = len(sentiments) // 2
        if mid > 0:
            old_avg = sum(sentiments[:mid]) / mid
            new_avg = sum(sentiments[mid:]) / (len(sentiments) - mid)
            if new_avg > old_avg + 0.1:
                trend = "improving"
            elif new_avg < old_avg - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Most common emotion
        from collections import Counter
        emotion_counts = Counter(emotions)
        dominant = emotion_counts.most_common(1)[0][0] if emotion_counts else "neutral"

        return {
            "average_sentiment": avg_sentiment,
            "dominant_emotion": dominant,
            "trend": trend,
            "emotion_distribution": dict(emotion_counts),
            "samples_analyzed": len(history),
            "recommendation": self._get_state_recommendation(avg_sentiment, trend),
        }

    def _get_recommended_action(self, emotion):
        """Get recommended trading action based on emotion."""
        actions = {
            "fear": "reduce_position_size",
            "anger": "pause_trading",
            "joy": "review_risk_levels",
            "sadness": "stick_to_plan",
            "surprise": "wait_for_confirmation",
            "trust": "proceed_with_caution",
        }
        return actions.get(emotion, "maintain_current_strategy")

    def _get_state_recommendation(self, avg_sentiment, trend):
        """Generate a recommendation based on emotional state."""
        if avg_sentiment < -0.3 and trend == "declining":
            return "Consider taking a break from active trading. Emotional state may impair judgment."
        elif avg_sentiment < -0.1:
            return "Exercise extra caution. Negative sentiment can lead to impulsive decisions."
        elif avg_sentiment > 0.3 and trend == "improving":
            return "Positive momentum detected. Be mindful of overconfidence bias."
        elif trend == "stable":
            return "Emotional state is stable. Good conditions for rational decision-making."
        return "Monitor emotional state and adjust trading activity accordingly."
