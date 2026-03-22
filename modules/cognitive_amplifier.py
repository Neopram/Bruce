"""
Bruce AI - Cognitive Amplification System

Proven techniques from AI research that make a 7B parameter model
perform like a much larger model. Implements Chain-of-Thought,
Self-Consistency, Reflection, Decomposition, RAG-Enhanced Reasoning,
Multi-Perspective Analysis, Confidence Calibration, and a SmartRouter
that auto-selects the best strategy per question.

All functions work with the existing LLMBridge from llm_bridge.py.
"""

import json
import logging
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("Bruce.CognitiveAmplifier")

BASE_DIR = Path(__file__).resolve().parent.parent
METRICS_PATH = BASE_DIR / "data" / "cognitive_metrics.json"


# ---------------------------------------------------------------------------
# Metrics persistence
# ---------------------------------------------------------------------------

def _load_metrics() -> Dict[str, Any]:
    """Load cognitive performance metrics from disk."""
    try:
        if METRICS_PATH.exists():
            return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to load cognitive metrics: %s", exc)
    return {
        "technique_usage": {},
        "technique_latency_ms": {},
        "technique_success": {},
        "total_queries": 0,
        "last_updated": None,
    }


def _save_metrics(metrics: Dict[str, Any]) -> None:
    """Persist cognitive performance metrics to disk."""
    try:
        METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
        metrics["last_updated"] = datetime.now(timezone.utc).isoformat()
        METRICS_PATH.write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning("Failed to save cognitive metrics: %s", exc)


def _record_metric(technique: str, latency_ms: float, success: bool) -> None:
    """Record a single technique invocation in the metrics store."""
    metrics = _load_metrics()
    metrics["total_queries"] = metrics.get("total_queries", 0) + 1

    usage = metrics.setdefault("technique_usage", {})
    usage[technique] = usage.get(technique, 0) + 1

    latencies = metrics.setdefault("technique_latency_ms", {})
    prev = latencies.get(technique, [])
    # Keep last 100 latency samples per technique
    prev.append(round(latency_ms, 1))
    latencies[technique] = prev[-100:]

    successes = metrics.setdefault("technique_success", {})
    bucket = successes.setdefault(technique, {"ok": 0, "fail": 0})
    bucket["ok" if success else "fail"] += 1

    _save_metrics(metrics)


# ---------------------------------------------------------------------------
# Helper: safe LLM call
# ---------------------------------------------------------------------------

def _llm_query(
    llm_client,
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.7,
    system_prompt: Optional[str] = None,
) -> str:
    """
    Call LLMBridge.query() with error handling.
    Returns the response string, or an empty string on failure.
    """
    try:
        result = llm_client.query(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
        )
        if result and not str(result).startswith("LLM error:"):
            return str(result).strip()
        logger.warning("LLM returned error: %s", result)
        return ""
    except Exception as exc:
        logger.error("LLM query failed: %s", exc)
        return ""


# ---------------------------------------------------------------------------
# 1. Chain of Thought (CoT)
# ---------------------------------------------------------------------------

def think_step_by_step(question: str, llm_client) -> Dict[str, Any]:
    """
    Wraps the question with chain-of-thought prompting so the model
    reasons explicitly before giving a final answer.

    Returns: {thinking: str, answer: str, confidence: float}
    """
    start = time.perf_counter()
    success = False

    try:
        prompt = (
            "Think through this step by step before giving your final answer.\n\n"
            f"Question: {question}\n\n"
            "Let me think about this carefully:\n"
            "Step 1:"
        )

        raw = _llm_query(llm_client, prompt, max_tokens=1024, temperature=0.3)
        if not raw:
            return {
                "thinking": "",
                "answer": "I was unable to generate a response.",
                "confidence": 0.0,
            }

        # Attempt to split thinking from final answer
        thinking = raw
        answer = raw

        # Look for common final-answer markers
        for marker in [
            "Final answer:", "Final Answer:", "FINAL ANSWER:",
            "Therefore,", "In conclusion,", "To summarize,",
            "The answer is:", "Answer:", "So,",
        ]:
            if marker in raw:
                parts = raw.split(marker, 1)
                thinking = parts[0].strip()
                answer = parts[1].strip()
                break

        # Estimate confidence by how structured the reasoning is
        step_count = len(re.findall(r"Step \d", thinking))
        has_conclusion = any(m in raw for m in ["therefore", "conclusion", "answer is"])
        confidence = min(1.0, 0.4 + step_count * 0.1 + (0.2 if has_conclusion else 0.0))

        success = True
        return {
            "thinking": thinking,
            "answer": answer,
            "confidence": round(confidence, 2),
        }
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        _record_metric("chain_of_thought", elapsed, success)
        logger.info("CoT completed in %.0f ms (success=%s)", elapsed, success)


# ---------------------------------------------------------------------------
# 2. Self-Consistency (SC)
# ---------------------------------------------------------------------------

def self_consistent_answer(
    question: str,
    llm_client,
    n_samples: int = 3,
) -> Dict[str, Any]:
    """
    Generate *n_samples* independent answers with temperature > 0 and
    select the majority answer.

    Returns: {answer: str, confidence: float, alternatives: list,
              agreement_rate: float}
    """
    start = time.perf_counter()
    success = False

    try:
        prompt = (
            f"Answer the following question concisely.\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        answers: List[str] = []
        for _ in range(n_samples):
            resp = _llm_query(llm_client, prompt, max_tokens=512, temperature=0.8)
            if resp:
                answers.append(resp)

        if not answers:
            return {
                "answer": "I was unable to generate consistent answers.",
                "confidence": 0.0,
                "alternatives": [],
                "agreement_rate": 0.0,
            }

        # Normalize answers for comparison (lowercase, strip punctuation)
        def _normalize(text: str) -> str:
            return re.sub(r"[^\w\s]", "", text.lower()).strip()

        normalized = [_normalize(a) for a in answers]

        # Find the most common answer (by normalized form)
        counter = Counter(normalized)
        most_common_norm, count = counter.most_common(1)[0]

        # Pick the original (un-normalized) version of the winning answer
        best_answer = answers[normalized.index(most_common_norm)]

        agreement_rate = count / len(answers)
        alternatives = [a for a in answers if _normalize(a) != most_common_norm]

        success = True
        return {
            "answer": best_answer,
            "confidence": round(agreement_rate, 2),
            "alternatives": alternatives[:5],
            "agreement_rate": round(agreement_rate, 2),
        }
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        _record_metric("self_consistency", elapsed, success)
        logger.info("SC completed in %.0f ms (success=%s)", elapsed, success)


# ---------------------------------------------------------------------------
# 3. Reflection & Self-Correction
# ---------------------------------------------------------------------------

def reflect_and_correct(
    question: str,
    initial_answer: str,
    llm_client,
) -> Dict[str, Any]:
    """
    Ask the model to critique and improve its own answer.

    Returns: {original: str, critique: str, improved: str, changes_made: list}
    """
    start = time.perf_counter()
    success = False

    try:
        critique_prompt = (
            "You are a careful reviewer. Examine the following question and "
            "answer for errors, biases, missing information, or logical flaws.\n\n"
            f"Question: {question}\n"
            f"Answer: {initial_answer}\n\n"
            "Critique (list specific issues):"
        )

        critique = _llm_query(llm_client, critique_prompt, max_tokens=512, temperature=0.3)

        if not critique or "no issues" in critique.lower() or "looks correct" in critique.lower():
            success = True
            return {
                "original": initial_answer,
                "critique": critique or "No issues found.",
                "improved": initial_answer,
                "changes_made": [],
            }

        improve_prompt = (
            "Based on the critique below, provide an improved answer to the question.\n\n"
            f"Question: {question}\n"
            f"Original answer: {initial_answer}\n"
            f"Critique: {critique}\n\n"
            "Improved answer:"
        )

        improved = _llm_query(llm_client, improve_prompt, max_tokens=512, temperature=0.3)
        if not improved:
            improved = initial_answer

        # Extract changes as bullet points from the critique
        changes = re.findall(r"[-*]\s*(.+?)(?:\n|$)", critique)
        if not changes:
            # Fall back: each sentence in the critique is a change
            changes = [s.strip() for s in critique.split(".") if len(s.strip()) > 10]

        success = True
        return {
            "original": initial_answer,
            "critique": critique,
            "improved": improved,
            "changes_made": changes[:10],
        }
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        _record_metric("reflection", elapsed, success)
        logger.info("Reflection completed in %.0f ms (success=%s)", elapsed, success)


# ---------------------------------------------------------------------------
# 4. Decomposition
# ---------------------------------------------------------------------------

def decompose_and_solve(question: str, llm_client) -> Dict[str, Any]:
    """
    Break a complex question into sub-questions, answer each
    independently, and synthesize a final answer.

    Returns: {sub_questions: list, sub_answers: list, synthesis: str}
    """
    start = time.perf_counter()
    success = False

    try:
        # Step 1 - decompose
        decompose_prompt = (
            "Break the following complex question into 2 to 5 simpler "
            "sub-questions that, when answered together, fully address "
            "the original question. Output ONLY a numbered list.\n\n"
            f"Question: {question}\n\n"
            "Sub-questions:"
        )

        decomp_raw = _llm_query(llm_client, decompose_prompt, max_tokens=512, temperature=0.3)

        # Parse numbered list
        sub_questions = re.findall(r"\d+[.)]\s*(.+?)(?:\n|$)", decomp_raw)
        if not sub_questions:
            # Fallback: split by newlines
            sub_questions = [
                line.strip().lstrip("- ").strip()
                for line in decomp_raw.split("\n")
                if line.strip() and len(line.strip()) > 5
            ]
        sub_questions = sub_questions[:5]  # cap at 5

        if not sub_questions:
            # Cannot decompose; answer directly
            direct = _llm_query(llm_client, question, max_tokens=512, temperature=0.3)
            success = bool(direct)
            return {
                "sub_questions": [],
                "sub_answers": [],
                "synthesis": direct or "Unable to decompose or answer.",
            }

        # Step 2 - answer each sub-question
        sub_answers: List[str] = []
        for sq in sub_questions:
            ans = _llm_query(
                llm_client,
                f"Answer this concisely:\n{sq}",
                max_tokens=384,
                temperature=0.3,
            )
            sub_answers.append(ans or "No answer available.")

        # Step 3 - synthesize
        qa_block = "\n".join(
            f"Q{i+1}: {sq}\nA{i+1}: {sa}"
            for i, (sq, sa) in enumerate(zip(sub_questions, sub_answers))
        )
        synthesis_prompt = (
            "Using the sub-answers below, provide a comprehensive answer "
            "to the original question.\n\n"
            f"Original question: {question}\n\n"
            f"{qa_block}\n\n"
            "Comprehensive answer:"
        )

        synthesis = _llm_query(llm_client, synthesis_prompt, max_tokens=768, temperature=0.3)
        success = bool(synthesis)

        return {
            "sub_questions": sub_questions,
            "sub_answers": sub_answers,
            "synthesis": synthesis or "Unable to synthesize answers.",
        }
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        _record_metric("decomposition", elapsed, success)
        logger.info("Decomposition completed in %.0f ms (success=%s)", elapsed, success)


# ---------------------------------------------------------------------------
# 5. RAG-Enhanced Reasoning
# ---------------------------------------------------------------------------

def rag_enhanced_answer(question: str, llm_client) -> Dict[str, Any]:
    """
    Search the knowledge base for relevant context, then generate an
    answer grounded in retrieved facts.

    Returns: {answer: str, sources: list, grounded: bool}
    """
    start = time.perf_counter()
    success = False

    try:
        # Try to import and use the RAG engine
        try:
            from modules.rag_engine import get_rag_engine
            rag = get_rag_engine()
            rag_result = rag.rag_query(question, top_k=5)
            augmented_prompt = rag_result.get("augmented_prompt", question)
            chunks = rag_result.get("chunks", [])
            sources = [
                {
                    "text": c.get("text", "")[:200],
                    "source": c.get("metadata", {}).get("source", "unknown"),
                    "relevance": c.get("relevance", 0),
                }
                for c in chunks
            ]
            grounded = len(chunks) > 0
        except Exception as exc:
            logger.debug("RAG engine unavailable, answering without context: %s", exc)
            augmented_prompt = question
            sources = []
            grounded = False

        answer = _llm_query(
            llm_client,
            augmented_prompt,
            max_tokens=768,
            temperature=0.3,
            system_prompt=(
                "You are a knowledgeable assistant. Answer based on the "
                "provided context when available. Be precise and factual."
            ),
        )

        success = bool(answer)
        return {
            "answer": answer or "Unable to generate an answer.",
            "sources": sources,
            "grounded": grounded,
        }
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        _record_metric("rag_enhanced", elapsed, success)
        logger.info("RAG-enhanced answer in %.0f ms (grounded=%s)", elapsed, success)


# ---------------------------------------------------------------------------
# 6. Multi-Perspective Analysis
# ---------------------------------------------------------------------------

_PERSPECTIVES = {
    "optimistic_analyst": (
        "You are an optimistic analyst. Focus on opportunities, positive "
        "outcomes, and strengths. Be enthusiastic but grounded in facts."
    ),
    "pessimistic_risk_manager": (
        "You are a pessimistic risk manager. Focus on risks, downsides, "
        "potential failures, and what could go wrong. Be thorough."
    ),
    "neutral_data_scientist": (
        "You are a neutral data scientist. Focus only on data, evidence, "
        "and measurable facts. Avoid opinions and speculation."
    ),
    "contrarian_trader": (
        "You are a contrarian thinker. Challenge the conventional wisdom. "
        "Present the opposite view and explain why the majority might be wrong."
    ),
}


def multi_perspective(question: str, llm_client) -> Dict[str, Any]:
    """
    Generate answers from multiple perspectives, then synthesize a
    balanced view.

    Returns: {perspectives: dict, synthesis: str, confidence: float}
    """
    start = time.perf_counter()
    success = False

    try:
        perspectives: Dict[str, str] = {}

        for name, system_prompt in _PERSPECTIVES.items():
            resp = _llm_query(
                llm_client,
                f"Analyze this from your perspective:\n\n{question}",
                max_tokens=384,
                temperature=0.5,
                system_prompt=system_prompt,
            )
            perspectives[name] = resp or "No perspective generated."

        # Synthesize
        views_block = "\n\n".join(
            f"[{name.replace('_', ' ').title()}]: {view}"
            for name, view in perspectives.items()
        )
        synthesis_prompt = (
            "You have received the following analyses from different "
            "perspectives. Synthesize them into a balanced, well-rounded "
            "answer. Highlight where perspectives agree and disagree.\n\n"
            f"Question: {question}\n\n"
            f"{views_block}\n\n"
            "Balanced synthesis:"
        )

        synthesis = _llm_query(llm_client, synthesis_prompt, max_tokens=768, temperature=0.3)

        # Confidence: higher when perspectives agree
        all_views = list(perspectives.values())
        # Simple heuristic: measure word overlap between perspectives
        word_sets = [set(re.findall(r"\w+", v.lower())) for v in all_views if v]
        if len(word_sets) >= 2:
            pairwise_overlaps = []
            for i in range(len(word_sets)):
                for j in range(i + 1, len(word_sets)):
                    union = word_sets[i] | word_sets[j]
                    intersection = word_sets[i] & word_sets[j]
                    if union:
                        pairwise_overlaps.append(len(intersection) / len(union))
            avg_overlap = sum(pairwise_overlaps) / len(pairwise_overlaps) if pairwise_overlaps else 0.5
            confidence = round(min(1.0, avg_overlap + 0.3), 2)
        else:
            confidence = 0.5

        success = bool(synthesis)
        return {
            "perspectives": perspectives,
            "synthesis": synthesis or "Unable to synthesize perspectives.",
            "confidence": confidence,
        }
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        _record_metric("multi_perspective", elapsed, success)
        logger.info("Multi-perspective completed in %.0f ms", elapsed)


# ---------------------------------------------------------------------------
# 7. Confidence Calibration
# ---------------------------------------------------------------------------

def calibrated_answer(question: str, llm_client) -> Dict[str, Any]:
    """
    Generate an answer, ask the model to self-assess confidence,
    and escalate to more powerful techniques if confidence is low.

    Returns: {answer: str, confidence: float, uncertainty_areas: list}
    """
    start = time.perf_counter()
    success = False

    try:
        # Step 1 - initial answer
        initial = _llm_query(
            llm_client, question, max_tokens=512, temperature=0.3
        )
        if not initial:
            return {
                "answer": "Unable to generate an answer.",
                "confidence": 0.0,
                "uncertainty_areas": ["Failed to generate any response."],
            }

        # Step 2 - self-assess
        assess_prompt = (
            "Rate your confidence in the following answer on a scale "
            "of 1 to 10 (10 = certain). Then list what could be wrong "
            "or missing. Use this EXACT format:\n"
            "Confidence: <number>\n"
            "Uncertainties:\n- <issue 1>\n- <issue 2>\n\n"
            f"Question: {question}\n"
            f"Answer: {initial}\n\n"
            "Assessment:"
        )

        assessment = _llm_query(llm_client, assess_prompt, max_tokens=256, temperature=0.2)

        # Parse confidence score
        conf_match = re.search(r"[Cc]onfidence[:\s]*(\d+(?:\.\d+)?)", assessment)
        raw_confidence = float(conf_match.group(1)) if conf_match else 5.0
        confidence = min(10.0, max(1.0, raw_confidence)) / 10.0

        # Parse uncertainty areas
        uncertainty_areas = re.findall(r"[-*]\s*(.+?)(?:\n|$)", assessment)
        if not uncertainty_areas:
            uncertainty_areas = [
                s.strip() for s in assessment.split("\n")
                if s.strip() and "confidence" not in s.lower() and len(s.strip()) > 10
            ]

        # Step 3 - if confidence is low, escalate
        answer = initial
        if confidence < 0.5:
            logger.info("Low confidence (%.2f), escalating to CoT + reflection", confidence)
            cot_result = think_step_by_step(question, llm_client)
            if cot_result["confidence"] > confidence:
                answer = cot_result["answer"]
                confidence = cot_result["confidence"]

            # Also try reflection
            reflection = reflect_and_correct(question, answer, llm_client)
            if reflection["changes_made"]:
                answer = reflection["improved"]
                confidence = min(1.0, confidence + 0.1)

        # If confidence still low, flag it
        if confidence < 0.5:
            answer = (
                f"I'm not fully confident in this answer (confidence: "
                f"{confidence:.0%}). {answer}"
            )

        success = True
        return {
            "answer": answer,
            "confidence": round(confidence, 2),
            "uncertainty_areas": uncertainty_areas[:5],
        }
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        _record_metric("calibrated", elapsed, success)
        logger.info("Calibrated answer in %.0f ms (conf=%.2f)", elapsed, confidence if success else 0)


# ---------------------------------------------------------------------------
# 9. Question Classifier (rule-based, no LLM needed)
# ---------------------------------------------------------------------------

_FACTUAL_PATTERNS = [
    r"^what (is|are|was|were)\b", r"^who (is|are|was|were)\b",
    r"^when (did|was|is|will)\b", r"^where (is|are|was|were)\b",
    r"^how many\b", r"^how much\b", r"^define\b", r"^name\b",
]
_ANALYTICAL_PATTERNS = [
    r"^why\b", r"^how does\b", r"^how do\b", r"^compare\b",
    r"^explain\b", r"^analyze\b", r"^analyse\b", r"^what causes\b",
    r"affect", r"impact", r"relationship between",
]
_PREDICTIVE_PATTERNS = [
    r"^will\b", r"^should (i|we)\b", r"^what will\b",
    r"^predict\b", r"forecast", r"future", r"expect",
]
_CREATIVE_PATTERNS = [
    r"^write\b", r"^create\b", r"^design\b", r"^generate\b",
    r"^compose\b", r"^draft\b", r"^brainstorm\b", r"^imagine\b",
]
_TRANSLATION_PATTERNS = [
    r"^translate\b", r"^say .+ in \w+", r"^how do you say\b",
    r"in spanish\b", r"in french\b", r"in chinese\b", r"in japanese\b",
    r"in german\b", r"in portuguese\b", r"in italian\b",
]
_MATH_PATTERNS = [
    r"\bcalculate\b", r"\bcompute\b", r"\bsolve\b",
    r"\d+\s*[\+\-\*/\^]\s*\d+", r"\bequation\b", r"\bformula\b",
    r"\bderivative\b", r"\bintegral\b", r"\bpercent\b",
]


def classify_question(question: str) -> Dict[str, Any]:
    """
    Rule-based question classifier (fast, no LLM call).

    Returns: {type: str, complexity: str, suggested_mode: str}
    """
    q_lower = question.lower().strip()

    def _matches(patterns):
        return any(re.search(p, q_lower) for p in patterns)

    # Determine type
    if _matches(_TRANSLATION_PATTERNS):
        q_type = "translation"
    elif _matches(_MATH_PATTERNS):
        q_type = "math"
    elif _matches(_CREATIVE_PATTERNS):
        q_type = "creative"
    elif _matches(_PREDICTIVE_PATTERNS):
        q_type = "predictive"
    elif _matches(_ANALYTICAL_PATTERNS):
        q_type = "analytical"
    elif _matches(_FACTUAL_PATTERNS):
        q_type = "factual"
    else:
        q_type = "general"

    # Estimate complexity
    word_count = len(q_lower.split())
    has_multiple_clauses = any(c in q_lower for c in [" and ", " but ", " or ", ",", ";"])
    has_conditionals = any(c in q_lower for c in ["if ", "assuming ", "given that"])

    if word_count > 30 or (has_multiple_clauses and has_conditionals):
        complexity = "complex"
    elif word_count > 15 or has_multiple_clauses or has_conditionals:
        complexity = "medium"
    else:
        complexity = "simple"

    # Map to suggested mode
    mode_map = {
        ("factual", "simple"): "fast",
        ("factual", "medium"): "thorough",
        ("factual", "complex"): "thorough",
        ("analytical", "simple"): "thorough",
        ("analytical", "medium"): "thorough",
        ("analytical", "complex"): "maximum",
        ("predictive", "simple"): "thorough",
        ("predictive", "medium"): "maximum",
        ("predictive", "complex"): "maximum",
        ("creative", "simple"): "fast",
        ("creative", "medium"): "fast",
        ("creative", "complex"): "thorough",
        ("translation", "simple"): "fast",
        ("translation", "medium"): "fast",
        ("translation", "complex"): "fast",
        ("math", "simple"): "thorough",
        ("math", "medium"): "thorough",
        ("math", "complex"): "maximum",
        ("general", "simple"): "fast",
        ("general", "medium"): "thorough",
        ("general", "complex"): "maximum",
    }
    suggested_mode = mode_map.get((q_type, complexity), "thorough")

    return {
        "type": q_type,
        "complexity": complexity,
        "suggested_mode": suggested_mode,
    }


# ---------------------------------------------------------------------------
# 8. SmartRouter - CognitiveAmplifier class
# ---------------------------------------------------------------------------

class CognitiveAmplifier:
    """
    Central router that auto-selects the best cognitive amplification
    technique based on question complexity and requested mode.
    """

    def __init__(self, llm_client):
        self.llm = llm_client

    def amplified_answer(
        self,
        question: str,
        mode: str = "auto",
    ) -> Dict[str, Any]:
        """
        Generate an amplified answer using the best technique(s).

        Modes:
            auto    - classify question and pick the right strategy
            fast    - direct answer with optional RAG (quickest)
            thorough - CoT + RAG + reflection
            maximum  - all techniques combined (slow but best quality)
        """
        start = time.perf_counter()

        classification = classify_question(question)
        effective_mode = mode if mode != "auto" else classification["suggested_mode"]

        logger.info(
            "CognitiveAmplifier: question_type=%s complexity=%s mode=%s->%s",
            classification["type"],
            classification["complexity"],
            mode,
            effective_mode,
        )

        try:
            if effective_mode == "fast":
                result = self._fast(question, classification)
            elif effective_mode == "thorough":
                result = self._thorough(question, classification)
            elif effective_mode == "maximum":
                result = self._maximum(question, classification)
            else:
                result = self._thorough(question, classification)
        except Exception as exc:
            logger.error("CognitiveAmplifier failed, falling back to direct: %s", exc)
            direct = _llm_query(self.llm, question, max_tokens=512, temperature=0.3)
            result = {
                "answer": direct or "An error occurred while processing your question.",
                "confidence": 0.3,
                "method": "fallback_direct",
            }

        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        result["classification"] = classification
        result["mode"] = effective_mode
        result["elapsed_ms"] = elapsed_ms

        _record_metric(f"amplified_{effective_mode}", elapsed_ms, bool(result.get("answer")))
        return result

    # -- Mode implementations -----------------------------------------------

    def _fast(self, question: str, classification: Dict) -> Dict[str, Any]:
        """Fast mode: RAG-enhanced direct answer."""
        rag_result = rag_enhanced_answer(question, self.llm)
        return {
            "answer": rag_result["answer"],
            "confidence": 0.6 if rag_result["grounded"] else 0.4,
            "method": "rag_direct",
            "sources": rag_result.get("sources", []),
            "grounded": rag_result["grounded"],
        }

    def _thorough(self, question: str, classification: Dict) -> Dict[str, Any]:
        """Thorough mode: CoT + RAG + reflection."""
        q_type = classification["type"]

        # Start with RAG context
        rag_result = rag_enhanced_answer(question, self.llm)
        base_answer = rag_result["answer"]
        sources = rag_result.get("sources", [])

        # For math/logic, prioritize CoT + self-consistency
        if q_type in ("math", "analytical"):
            cot = think_step_by_step(question, self.llm)
            base_answer = cot["answer"]
            confidence = cot["confidence"]
        else:
            confidence = 0.6 if rag_result["grounded"] else 0.4

        # Reflect and correct
        reflection = reflect_and_correct(question, base_answer, self.llm)
        final_answer = reflection["improved"]

        if reflection["changes_made"]:
            confidence = min(1.0, confidence + 0.1)

        return {
            "answer": final_answer,
            "confidence": round(confidence, 2),
            "method": "cot_rag_reflection" if q_type in ("math", "analytical") else "rag_reflection",
            "sources": sources,
            "thinking": cot["thinking"] if q_type in ("math", "analytical") else None,
            "changes_made": reflection["changes_made"],
        }

    def _maximum(self, question: str, classification: Dict) -> Dict[str, Any]:
        """Maximum mode: all techniques combined."""
        q_type = classification["type"]

        # 1. Decompose if complex
        decomp = decompose_and_solve(question, self.llm)

        # 2. Multi-perspective analysis
        perspectives = multi_perspective(question, self.llm)

        # 3. Chain of thought
        cot = think_step_by_step(question, self.llm)

        # 4. Self-consistency check
        sc = self_consistent_answer(question, self.llm, n_samples=3)

        # 5. RAG grounding
        rag_result = rag_enhanced_answer(question, self.llm)

        # 6. Synthesize all signals
        all_answers = [
            decomp.get("synthesis", ""),
            perspectives.get("synthesis", ""),
            cot.get("answer", ""),
            sc.get("answer", ""),
            rag_result.get("answer", ""),
        ]
        all_answers = [a for a in all_answers if a and len(a) > 10]

        synthesis_prompt = (
            "You have multiple analyses of the same question. "
            "Synthesize the best possible answer, keeping only "
            "the most accurate and well-supported points.\n\n"
            f"Question: {question}\n\n"
            + "\n\n".join(
                f"Analysis {i+1}: {a}" for i, a in enumerate(all_answers)
            )
            + "\n\nBest synthesized answer:"
        )

        final = _llm_query(self.llm, synthesis_prompt, max_tokens=1024, temperature=0.2)

        # 7. Final reflection
        reflection = reflect_and_correct(question, final or all_answers[0] if all_answers else "", self.llm)

        # 8. Calibrate confidence
        confidences = [
            cot.get("confidence", 0.5),
            sc.get("agreement_rate", 0.5),
            perspectives.get("confidence", 0.5),
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        return {
            "answer": reflection["improved"],
            "confidence": round(avg_confidence, 2),
            "method": "maximum_all_techniques",
            "decomposition": {
                "sub_questions": decomp.get("sub_questions", []),
                "synthesis": decomp.get("synthesis", ""),
            },
            "perspectives": perspectives.get("perspectives", {}),
            "thinking": cot.get("thinking", ""),
            "self_consistency": {
                "agreement_rate": sc.get("agreement_rate", 0),
                "alternatives": sc.get("alternatives", []),
            },
            "sources": rag_result.get("sources", []),
            "reflection": {
                "changes_made": reflection.get("changes_made", []),
            },
        }


# ---------------------------------------------------------------------------
# Integration: drop-in replacement for direct LLM calls
# ---------------------------------------------------------------------------

_amplifier_instance: Optional[CognitiveAmplifier] = None


def get_amplifier(llm_client) -> CognitiveAmplifier:
    """Get or create a singleton CognitiveAmplifier."""
    global _amplifier_instance
    if _amplifier_instance is None or _amplifier_instance.llm is not llm_client:
        _amplifier_instance = CognitiveAmplifier(llm_client)
    return _amplifier_instance


def amplified_query(
    llm_client,
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.7,
    system_prompt: Optional[str] = None,
    mode: str = "auto",
) -> str:
    """
    Drop-in replacement for LLMBridge.query().

    When the CognitiveAmplifier is available, routes the prompt through
    the amplification pipeline. Falls back to a direct LLM call on error.

    Returns a plain string response, matching the LLMBridge.query() signature.
    """
    try:
        amp = get_amplifier(llm_client)
        result = amp.amplified_answer(prompt, mode=mode)
        answer = result.get("answer", "")
        if answer:
            return answer
    except Exception as exc:
        logger.warning("Amplified query failed, falling back to direct: %s", exc)

    # Fallback to direct call
    return llm_client.query(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        system_prompt=system_prompt,
    )


def get_cognitive_metrics() -> Dict[str, Any]:
    """Return the current cognitive performance metrics."""
    return _load_metrics()
