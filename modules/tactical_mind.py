"""
Tactical planning module.
Builds a tree of tactical objectives, breaks complex goals into steps,
prioritizes using dependency-aware scheduling, tracks execution, and adapts on failure.
"""
from datetime import datetime
from collections import deque


class TacticalMind:
    """Builds and manages a tree of tactical objectives linked to goals."""

    def __init__(self):
        self.tactics = {}
        self.execution_log = []
        self.failure_adaptations = []

    def add_tactic(self, name, description, goal, dependencies=None, priority=5, deadline=None):
        """Add a tactic to the plan with optional priority and deadline."""
        self.tactics[name] = {
            "description": description,
            "goal": goal,
            "dependencies": dependencies or [],
            "priority": priority,
            "deadline": deadline,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "retries": 0,
        }
        return {"added": name, "total_tactics": len(self.tactics)}

    def remove_tactic(self, name):
        """Remove a tactic from the plan."""
        if name in self.tactics:
            del self.tactics[name]
            return {"removed": name}
        return {"status": "error", "message": f"Tactic '{name}' not found"}

    def plan_sequence(self):
        """Generate an execution sequence respecting dependencies (topological sort)."""
        visited = set()
        sequence = []
        temp_mark = set()

        def visit(name):
            if name in temp_mark:
                return  # Cycle detected, skip
            if name in visited:
                return
            temp_mark.add(name)
            tactic = self.tactics.get(name)
            if tactic:
                for dep in tactic["dependencies"]:
                    if dep in self.tactics:
                        visit(dep)
            temp_mark.discard(name)
            visited.add(name)
            sequence.append(name)

        sorted_names = sorted(
            self.tactics.keys(),
            key=lambda n: self.tactics[n].get("priority", 5),
            reverse=True,
        )
        for name in sorted_names:
            if name not in visited:
                visit(name)

        return sequence

    def execute_plan(self, executor_fn=None):
        """Execute the planned sequence of tactics."""
        sequence = self.plan_sequence()
        results = []

        for name in sequence:
            tactic = self.tactics[name]
            if tactic["status"] == "completed":
                continue

            deps_met = all(
                self.tactics.get(dep, {}).get("status") == "completed"
                for dep in tactic["dependencies"]
            )
            if not deps_met:
                results.append({"tactic": name, "status": "blocked", "reason": "unmet_dependencies"})
                continue

            tactic["status"] = "in_progress"
            try:
                if executor_fn:
                    outcome = executor_fn(name, tactic)
                else:
                    outcome = {"success": True}

                if outcome.get("success", False):
                    tactic["status"] = "completed"
                    tactic["completed_at"] = datetime.utcnow().isoformat()
                    results.append({"tactic": name, "status": "completed"})
                else:
                    tactic["status"] = "failed"
                    tactic["retries"] += 1
                    adaptation = self._adapt_on_failure(name, tactic, outcome)
                    results.append({"tactic": name, "status": "failed", "adaptation": adaptation})
            except Exception as e:
                tactic["status"] = "failed"
                tactic["retries"] += 1
                results.append({"tactic": name, "status": "error", "message": str(e)})

        self.execution_log.append({
            "sequence": sequence,
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
        })
        return results

    def _adapt_on_failure(self, name, tactic, outcome):
        """Adapt strategy when a tactic fails."""
        adaptation = {
            "tactic": name,
            "retry_count": tactic["retries"],
            "timestamp": datetime.utcnow().isoformat(),
        }

        if tactic["retries"] >= 3:
            adaptation["action"] = "abandon"
            adaptation["message"] = f"Tactic '{name}' abandoned after {tactic['retries']} retries"
            tactic["status"] = "abandoned"
        elif tactic["retries"] >= 2:
            adaptation["action"] = "simplify"
            adaptation["message"] = f"Simplifying tactic '{name}' for retry"
            tactic["status"] = "pending"
            tactic["priority"] = max(1, tactic["priority"] - 1)
        else:
            adaptation["action"] = "retry"
            adaptation["message"] = f"Retrying tactic '{name}'"
            tactic["status"] = "pending"

        self.failure_adaptations.append(adaptation)
        return adaptation

    def evaluate_progress(self, reports=None):
        """Evaluate progress of all tactics."""
        results = {}
        for name, tactic in self.tactics.items():
            deps_satisfied = all(
                self.tactics.get(dep, {}).get("status") == "completed"
                for dep in tactic["dependencies"]
            )
            goal_met = tactic["status"] == "completed"
            if reports:
                goal_met = goal_met or reports.get(name, False)

            results[name] = {
                "status": tactic["status"],
                "goal_met": goal_met,
                "dependencies_satisfied": deps_satisfied,
                "priority": tactic["priority"],
                "retries": tactic["retries"],
            }

        completed = sum(1 for r in results.values() if r["goal_met"])
        total = len(results)
        return {
            "tactics": results,
            "progress_pct": round(completed / total * 100, 1) if total else 0,
            "completed": completed,
            "total": total,
        }

    def break_down_goal(self, goal_name, subtasks):
        """Break a complex goal into ordered subtasks."""
        for i, subtask in enumerate(subtasks):
            deps = [subtasks[i - 1]["name"]] if i > 0 else []
            self.add_tactic(
                name=subtask["name"],
                description=subtask.get("description", ""),
                goal=goal_name,
                dependencies=deps,
                priority=subtask.get("priority", 5 - i),
            )
        return {"goal": goal_name, "subtasks_created": len(subtasks)}

    def get_execution_log(self, limit=10):
        """Return recent execution logs."""
        return self.execution_log[-limit:]

    def get_status(self):
        """Return tactical planning status."""
        statuses = {}
        for name, t in self.tactics.items():
            s = t["status"]
            statuses[s] = statuses.get(s, 0) + 1
        return {
            "total_tactics": len(self.tactics),
            "status_breakdown": statuses,
            "failure_adaptations": len(self.failure_adaptations),
        }
