#!/usr/bin/env python3
"""
Train Bruce AI - RLHF Pipeline
Analyzes user feedback data to improve model selection and response quality.
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
os.makedirs(os.path.join(DATA_DIR, "evaluations"), exist_ok=True)


def load_feedback_data() -> list:
    """Load feedback data from various feedback storage locations."""
    feedback_entries = []

    # Check logs directory for feedback files
    feedback_paths = [
        os.path.join(LOGS_DIR, "feedback.jsonl"),
        os.path.join(LOGS_DIR, "user_feedback.jsonl"),
        os.path.join(DATA_DIR, "feedback.jsonl"),
        os.path.join(PROJECT_ROOT, "feedback_data.jsonl"),
    ]

    for path in feedback_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                            feedback_entries.append(entry)
                        except json.JSONDecodeError:
                            continue
                print(f"  Loaded {len(feedback_entries)} entries from {path}")
            except Exception as e:
                print(f"  Warning: Could not read {path}: {e}")

    # If no real feedback found, generate synthetic for demonstration
    if not feedback_entries:
        print("  No feedback data found. Generating synthetic feedback for demonstration...")
        feedback_entries = generate_synthetic_feedback(50)

    return feedback_entries


def generate_synthetic_feedback(count: int = 50) -> list:
    """Generate synthetic feedback data for testing the pipeline."""
    import random
    random.seed(42)

    models = ["deepseek", "phi3", "gpt4", "claude"]
    tasks = ["trading_analysis", "shipping_query", "crypto_analysis", "general_chat",
             "risk_assessment", "market_prediction", "route_optimization"]
    feedback_entries = []

    for i in range(count):
        model = random.choice(models)
        task = random.choice(tasks)

        # Simulate model quality per task
        base_rating = {
            ("deepseek", "trading_analysis"): 4.2,
            ("deepseek", "crypto_analysis"): 4.0,
            ("phi3", "general_chat"): 4.5,
            ("phi3", "shipping_query"): 3.8,
            ("gpt4", "trading_analysis"): 4.5,
            ("gpt4", "risk_assessment"): 4.7,
            ("claude", "general_chat"): 4.8,
            ("claude", "shipping_query"): 4.3,
        }.get((model, task), 3.5)

        rating = max(1, min(5, round(base_rating + random.gauss(0, 0.5))))
        response_length = random.randint(50, 500)
        response_time = random.uniform(0.5, 5.0)
        detail_level = random.choice(["low", "medium", "high"])

        entry = {
            "id": f"fb_{i:04d}",
            "timestamp": datetime(2024, 1, 1 + i % 28, 10 + i % 12).isoformat(),
            "model": model,
            "task_type": task,
            "rating": rating,
            "response_length": response_length,
            "response_time_s": round(response_time, 2),
            "detail_level": detail_level,
            "thumbs_up": rating >= 4,
            "comment": "" if random.random() > 0.3 else random.choice([
                "Very helpful analysis",
                "Too slow",
                "Good detail but could be more concise",
                "Excellent response",
                "Not accurate enough",
                "Perfect for my needs",
            ]),
        }
        feedback_entries.append(entry)

    return feedback_entries


def analyze_feedback(entries: list) -> dict:
    """Analyze feedback patterns and generate insights."""
    analysis = {
        "total_entries": len(entries),
        "model_performance": {},
        "task_performance": {},
        "model_task_matrix": {},
        "positive_patterns": {},
        "negative_patterns": {},
        "recommendations": [],
    }

    # Group by model
    by_model = defaultdict(list)
    by_task = defaultdict(list)
    by_model_task = defaultdict(list)

    for entry in entries:
        model = entry.get("model", "unknown")
        task = entry.get("task_type", "unknown")
        rating = entry.get("rating", 3)

        by_model[model].append(entry)
        by_task[task].append(entry)
        by_model_task[(model, task)].append(entry)

    # Model performance
    for model, model_entries in by_model.items():
        ratings = [e.get("rating", 3) for e in model_entries]
        lengths = [e.get("response_length", 0) for e in model_entries]
        times = [e.get("response_time_s", 0) for e in model_entries]
        thumbs = [e.get("thumbs_up", False) for e in model_entries]

        analysis["model_performance"][model] = {
            "count": len(model_entries),
            "avg_rating": round(sum(ratings) / len(ratings), 2),
            "median_rating": sorted(ratings)[len(ratings) // 2],
            "thumbs_up_rate": round(sum(thumbs) / len(thumbs) * 100, 1),
            "avg_response_length": round(sum(lengths) / len(lengths)),
            "avg_response_time_s": round(sum(times) / len(times), 2),
        }

    # Task performance
    for task, task_entries in by_task.items():
        ratings = [e.get("rating", 3) for e in task_entries]
        analysis["task_performance"][task] = {
            "count": len(task_entries),
            "avg_rating": round(sum(ratings) / len(ratings), 2),
        }

    # Model-task matrix (which model is best for each task)
    for (model, task), mt_entries in by_model_task.items():
        ratings = [e.get("rating", 3) for e in mt_entries]
        key = f"{model}|{task}"
        analysis["model_task_matrix"][key] = {
            "count": len(mt_entries),
            "avg_rating": round(sum(ratings) / len(ratings), 2),
        }

    # Analyze positive patterns (rating >= 4)
    positive = [e for e in entries if e.get("rating", 0) >= 4]
    negative = [e for e in entries if e.get("rating", 0) <= 2]

    if positive:
        pos_lengths = [e.get("response_length", 0) for e in positive]
        pos_details = [e.get("detail_level", "") for e in positive]
        analysis["positive_patterns"] = {
            "count": len(positive),
            "avg_length": round(sum(pos_lengths) / len(pos_lengths)),
            "detail_distribution": {
                level: pos_details.count(level) for level in set(pos_details) if level
            },
        }

    if negative:
        neg_lengths = [e.get("response_length", 0) for e in negative]
        neg_details = [e.get("detail_level", "") for e in negative]
        analysis["negative_patterns"] = {
            "count": len(negative),
            "avg_length": round(sum(neg_lengths) / len(neg_lengths)),
            "detail_distribution": {
                level: neg_details.count(level) for level in set(neg_details) if level
            },
        }

    # Generate recommendations
    best_per_task = {}
    for (model, task), mt_entries in by_model_task.items():
        ratings = [e.get("rating", 3) for e in mt_entries]
        avg = sum(ratings) / len(ratings)
        if task not in best_per_task or avg > best_per_task[task][1]:
            best_per_task[task] = (model, avg, len(mt_entries))

    for task, (model, avg, count) in best_per_task.items():
        analysis["recommendations"].append({
            "task": task,
            "recommended_model": model,
            "avg_rating": round(avg, 2),
            "sample_size": count,
        })

    return analysis


def generate_model_preferences(analysis: dict) -> dict:
    """Generate model preference configuration based on feedback analysis."""
    preferences = {"task_routing": {}, "default_model": None, "updated_at": datetime.utcnow().isoformat()}

    # Route tasks to best-performing models
    for rec in analysis.get("recommendations", []):
        preferences["task_routing"][rec["task"]] = {
            "model": rec["recommended_model"],
            "confidence": round(rec["avg_rating"] / 5.0, 2),
            "samples": rec["sample_size"],
        }

    # Determine overall best model
    model_perf = analysis.get("model_performance", {})
    if model_perf:
        best_model = max(model_perf.items(), key=lambda x: x[1].get("avg_rating", 0))
        preferences["default_model"] = best_model[0]

    return preferences


def print_report(analysis: dict):
    """Print a formatted analysis report."""
    print(f"\n{'='*70}")
    print(f"  RLHF Analysis Report")
    print(f"  Total feedback entries: {analysis['total_entries']}")
    print(f"{'='*70}")

    # Model performance
    print(f"\n  Model Performance:")
    print(f"  {'Model':<15} {'Count':<8} {'Avg Rating':<12} {'Thumbs Up':<12} {'Avg Time':<10}")
    print(f"  {'-'*57}")
    for model, stats in sorted(analysis["model_performance"].items(),
                                key=lambda x: x[1]["avg_rating"], reverse=True):
        print(f"  {model:<15} {stats['count']:<8} {stats['avg_rating']:<12} "
              f"{stats['thumbs_up_rate']}%{'':<6} {stats['avg_response_time_s']}s")

    # Task performance
    print(f"\n  Task Performance:")
    print(f"  {'Task':<25} {'Count':<8} {'Avg Rating':<12}")
    print(f"  {'-'*45}")
    for task, stats in sorted(analysis["task_performance"].items(),
                               key=lambda x: x[1]["avg_rating"], reverse=True):
        print(f"  {task:<25} {stats['count']:<8} {stats['avg_rating']:<12}")

    # Recommendations
    print(f"\n  Model Routing Recommendations:")
    print(f"  {'Task':<25} {'Best Model':<15} {'Avg Rating':<12} {'Samples':<8}")
    print(f"  {'-'*60}")
    for rec in sorted(analysis["recommendations"], key=lambda x: x["avg_rating"], reverse=True):
        print(f"  {rec['task']:<25} {rec['recommended_model']:<15} "
              f"{rec['avg_rating']:<12} {rec['sample_size']:<8}")

    # Patterns
    if analysis["positive_patterns"]:
        pp = analysis["positive_patterns"]
        print(f"\n  Positive Response Patterns (rating >= 4):")
        print(f"    Count: {pp['count']}")
        print(f"    Avg length: {pp['avg_length']} chars")
        print(f"    Detail levels: {pp.get('detail_distribution', {})}")

    if analysis["negative_patterns"]:
        np_ = analysis["negative_patterns"]
        print(f"\n  Negative Response Patterns (rating <= 2):")
        print(f"    Count: {np_['count']}")
        print(f"    Avg length: {np_['avg_length']} chars")
        print(f"    Detail levels: {np_.get('detail_distribution', {})}")

    print(f"\n{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="RLHF training pipeline for Bruce AI")
    parser.add_argument("--min-feedback", type=int, default=10,
                        help="Minimum feedback entries required to run analysis")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Bruce AI - RLHF Training Pipeline")
    print(f"  Minimum feedback required: {args.min_feedback}")
    print(f"{'='*60}\n")

    start_time = time.time()

    # Load feedback
    entries = load_feedback_data()
    print(f"  Total feedback entries: {len(entries)}")

    if len(entries) < args.min_feedback:
        print(f"\n  Insufficient feedback ({len(entries)} < {args.min_feedback}). Aborting.")
        print(f"  Collect more feedback before running RLHF training.")
        sys.exit(1)

    # Analyze
    print("\n  Analyzing feedback patterns...")
    analysis = analyze_feedback(entries)

    # Generate model preferences
    preferences = generate_model_preferences(analysis)

    # Print report
    print_report(analysis)

    # Save outputs
    elapsed = time.time() - start_time

    report_path = os.path.join(DATA_DIR, "evaluations", "rlhf_report.json")
    with open(report_path, "w") as f:
        json.dump(analysis, f, indent=2)
    print(f"  Analysis report saved to {report_path}")

    prefs_path = os.path.join(MODELS_DIR, "model_preferences.json")
    with open(prefs_path, "w") as f:
        json.dump(preferences, f, indent=2)
    print(f"  Model preferences saved to {prefs_path}")

    print(f"\n  RLHF pipeline completed in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
