"""
introspector.py - Bruce's Cognitive Introspection Module
Scans backend files, functions, and routes to report unused or disconnected capabilities.
Extended with self-analysis of past decisions, pattern detection, quality scoring,
and periodic introspection reports.
"""

import os
import ast
import json
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("Bruce.Introspector")
logger.setLevel(logging.INFO)

INTROSPECTION_LOG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "logs", "introspection.jsonl"
)
os.makedirs(os.path.dirname(INTROSPECTION_LOG), exist_ok=True)


class BruceIntrospector:
    def __init__(self, base_path=".", exclude_dirs=None):
        self.base_path = base_path
        self.exclude_dirs = exclude_dirs or {
            "__pycache__", "venv", ".git", "node_modules", ".vscode", "public", "logs", "snapshots"
        }
        self.backend_files: List[str] = []
        self.function_map: Dict[str, List[str]] = {}
        self.route_map: Dict[str, str] = {}
        # Decision analysis storage
        self._decisions: List[dict] = []
        self._quality_scores: List[dict] = []
        self._load_history()

    # ------------------------------------------------------------------ #
    #  History persistence
    # ------------------------------------------------------------------ #

    def _load_history(self):
        """Load past introspection records from disk."""
        if not os.path.exists(INTROSPECTION_LOG):
            return
        try:
            with open(INTROSPECTION_LOG, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        rec_type = rec.get("type", "")
                        if rec_type == "decision":
                            self._decisions.append(rec)
                        elif rec_type == "quality_score":
                            self._quality_scores.append(rec)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

    def _persist(self, record: dict):
        """Append a record to the introspection log."""
        try:
            with open(INTROSPECTION_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"[Introspector] Could not persist: {e}")

    # ------------------------------------------------------------------ #
    #  Code scanning (preserved from original)
    # ------------------------------------------------------------------ #

    def scan_backend(self):
        """Walk the project tree and collect Python files."""
        self.backend_files = []
        for root, _, files in os.walk(self.base_path):
            if any(ignored in root for ignored in self.exclude_dirs):
                continue
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    self.backend_files.append(full_path)

    def extract_functions(self):
        """Extract function definitions from all scanned files."""
        self.function_map = {}
        for path in self.backend_files:
            try:
                with open(path, "r", encoding="utf-8-sig") as file:
                    content = file.read()
                    tree = ast.parse(content)
                    functions = [
                        node.name for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef) and not node.name.startswith("__")
                    ]
                    if functions:
                        rel_path = os.path.relpath(path, self.base_path)
                        self.function_map[rel_path] = functions
            except Exception as e:
                logger.debug(f"Error reading {path}: {e}")

    def extract_routes(self):
        """Extract files that contain FastAPI router decorators."""
        self.route_map = {}
        for path in self.backend_files:
            try:
                with open(path, "r", encoding="utf-8-sig") as file:
                    content = file.read()
                    if "@router." in content or "@app." in content:
                        rel_path = os.path.relpath(path, self.base_path)
                        self.route_map[rel_path] = content
            except Exception as e:
                logger.debug(f"Error parsing routes in {path}: {e}")

    def compare_functions_vs_routes(self) -> Dict[str, List[str]]:
        """Find functions that are not connected to any route."""
        routed_functions = set()
        for route_code in self.route_map.values():
            try:
                tree = ast.parse(route_code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        routed_functions.add(node.name)
            except Exception:
                continue

        unused = {}
        for path, functions in self.function_map.items():
            disconnected = [fn for fn in functions if fn not in routed_functions]
            if disconnected:
                unused[path] = disconnected
        return unused

    def generate_report(self) -> dict:
        """Generate a full code introspection report."""
        self.scan_backend()
        self.extract_functions()
        self.extract_routes()
        unused = self.compare_functions_vs_routes()
        return {
            "total_files_scanned": len(self.backend_files),
            "total_functions": sum(len(v) for v in self.function_map.values()),
            "total_routes": len(self.route_map),
            "disconnected_functions": unused,
            "total_disconnected": sum(len(v) for v in unused.values()),
        }

    # ------------------------------------------------------------------ #
    #  Decision analysis
    # ------------------------------------------------------------------ #

    def record_decision(
        self,
        decision: str,
        context: str,
        outcome: Optional[str] = None,
        confidence: float = 0.5,
        user_id: str = "system",
    ) -> dict:
        """
        Record a decision for later analysis.
        """
        record = {
            "type": "decision",
            "decision": decision,
            "context": context,
            "outcome": outcome,
            "confidence": confidence,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._decisions.append(record)
        self._persist(record)
        logger.info(f"[Introspector] Recorded decision: {decision[:60]}")
        return record

    def analyze_decisions(self, user_id: Optional[str] = None, limit: int = 50) -> dict:
        """
        Analyze past decisions to identify patterns and quality trends.
        """
        decisions = self._decisions
        if user_id:
            decisions = [d for d in decisions if d.get("user_id") == user_id]

        decisions = decisions[-limit:]

        if not decisions:
            return {"total": 0, "patterns": [], "avg_confidence": 0.0}

        # Confidence trend
        confidences = [d.get("confidence", 0.5) for d in decisions]
        avg_conf = sum(confidences) / len(confidences)

        # Outcome analysis
        outcomes = {}
        for d in decisions:
            o = d.get("outcome") or "pending"
            outcomes[o] = outcomes.get(o, 0) + 1

        # Pattern detection: find repeated decision themes via keyword extraction
        patterns = self._detect_patterns(decisions)

        return {
            "total": len(decisions),
            "avg_confidence": round(avg_conf, 3),
            "outcome_distribution": outcomes,
            "patterns": patterns,
            "confidence_trend": confidences[-20:],
        }

    def _detect_patterns(self, decisions: List[dict]) -> List[dict]:
        """
        Simple pattern detection: find frequently co-occurring keywords
        in decision contexts.
        """
        word_freq: Dict[str, int] = {}
        for d in decisions:
            text = f"{d.get('decision', '')} {d.get('context', '')}".lower()
            tokens = set(re.findall(r"\w{4,}", text))  # words with 4+ chars
            for token in tokens:
                word_freq[token] = word_freq.get(token, 0) + 1

        # Find words that appear in >20% of decisions
        threshold = max(2, len(decisions) * 0.2)
        frequent = {word: count for word, count in word_freq.items() if count >= threshold}

        patterns = []
        if frequent:
            sorted_words = sorted(frequent.items(), key=lambda x: x[1], reverse=True)[:10]
            for word, count in sorted_words:
                patterns.append({
                    "keyword": word,
                    "occurrences": count,
                    "frequency": round(count / len(decisions), 3),
                })

        return patterns

    # ------------------------------------------------------------------ #
    #  Quality scoring
    # ------------------------------------------------------------------ #

    def score_response(
        self,
        response: str,
        context: str,
        user_feedback: Optional[str] = None,
        user_id: str = "system",
    ) -> dict:
        """
        Score a response for quality based on heuristics.
        Factors: length, specificity, structure, relevance.
        """
        scores = {}

        # Length score (penalize very short or very long responses)
        length = len(response)
        if length < 20:
            scores["length"] = 0.2
        elif length < 50:
            scores["length"] = 0.5
        elif length < 500:
            scores["length"] = 0.9
        elif length < 2000:
            scores["length"] = 0.8
        else:
            scores["length"] = 0.6

        # Structure: does it have paragraphs, lists, etc.?
        has_structure = bool(
            re.search(r"\n\n|\n-|\n\d\.", response)
            or len(response.split("\n")) > 2
        )
        scores["structure"] = 0.8 if has_structure else 0.4

        # Specificity: ratio of unique long words
        words = re.findall(r"\w{4,}", response.lower())
        unique_ratio = len(set(words)) / max(len(words), 1)
        scores["specificity"] = round(min(unique_ratio * 1.5, 1.0), 3)

        # Relevance: keyword overlap with context
        ctx_keywords = set(re.findall(r"\w{4,}", context.lower()))
        resp_keywords = set(re.findall(r"\w{4,}", response.lower()))
        if ctx_keywords:
            overlap = len(ctx_keywords & resp_keywords) / len(ctx_keywords)
            scores["relevance"] = round(min(overlap * 2, 1.0), 3)
        else:
            scores["relevance"] = 0.5

        # User feedback bonus
        if user_feedback:
            fb_lower = user_feedback.lower()
            if any(w in fb_lower for w in ["good", "great", "thanks", "perfect", "helpful"]):
                scores["user_feedback"] = 0.9
            elif any(w in fb_lower for w in ["bad", "wrong", "useless", "incorrect"]):
                scores["user_feedback"] = 0.2
            else:
                scores["user_feedback"] = 0.5

        # Overall quality
        overall = sum(scores.values()) / len(scores)

        record = {
            "type": "quality_score",
            "scores": scores,
            "overall": round(overall, 3),
            "user_id": user_id,
            "response_length": length,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._quality_scores.append(record)
        self._persist(record)

        return record

    def get_quality_trend(self, user_id: Optional[str] = None, limit: int = 20) -> dict:
        """Get the quality score trend over recent responses."""
        scores = self._quality_scores
        if user_id:
            scores = [s for s in scores if s.get("user_id") == user_id]
        scores = scores[-limit:]

        if not scores:
            return {"total": 0, "avg_quality": 0.0, "trend": []}

        overall_values = [s.get("overall", 0) for s in scores]
        return {
            "total": len(scores),
            "avg_quality": round(sum(overall_values) / len(overall_values), 3),
            "trend": overall_values,
            "latest": scores[-1] if scores else None,
        }

    # ------------------------------------------------------------------ #
    #  Periodic introspection report
    # ------------------------------------------------------------------ #

    def periodic_report(self, user_id: Optional[str] = None) -> dict:
        """
        Generate a comprehensive introspection report combining code analysis,
        decision patterns, and quality metrics.
        """
        # Code analysis
        code_report = self.generate_report()

        # Decision analysis
        decision_analysis = self.analyze_decisions(user_id=user_id)

        # Quality trend
        quality = self.get_quality_trend(user_id=user_id)

        # Recommendations
        recommendations = []
        if code_report.get("total_disconnected", 0) > 5:
            recommendations.append(
                f"There are {code_report['total_disconnected']} disconnected functions. "
                "Consider connecting them to routes or removing dead code."
            )
        if decision_analysis.get("avg_confidence", 0) < 0.4:
            recommendations.append(
                "Average decision confidence is low. Consider gathering more data before acting."
            )
        if quality.get("avg_quality", 0) < 0.5:
            recommendations.append(
                "Response quality scores are below average. Review response structure and relevance."
            )
        if not recommendations:
            recommendations.append("All systems operating within normal parameters.")

        report = {
            "report_type": "periodic_introspection",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "code_analysis": code_report,
            "decision_analysis": decision_analysis,
            "quality_metrics": quality,
            "recommendations": recommendations,
        }

        # Persist the report
        report_record = {"type": "periodic_report", **report}
        self._persist(report_record)

        return report


if __name__ == "__main__":
    inspector = BruceIntrospector(base_path=".")
    report = inspector.generate_report()
    print(json.dumps(report, indent=2))
