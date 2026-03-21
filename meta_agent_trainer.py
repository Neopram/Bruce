# Crea y entrena agentes especializados
import time
import uuid
from collections import defaultdict


class MetaAgentTrainer:
    """Creates, trains, evaluates, and selects specialized agents."""

    def __init__(self):
        self._agents = {}
        self._training_history = defaultdict(list)
        self._evaluation_results = defaultdict(list)

    def register_agent(self, name, capabilities):
        """Register a new specialized agent with a set of capabilities.

        Args:
            name: Unique agent name.
            capabilities: List of strings describing what the agent can do.
        """
        agent_id = str(uuid.uuid4())[:8]
        self._agents[name] = {
            "id": agent_id,
            "name": name,
            "capabilities": list(capabilities),
            "status": "registered",
            "created_at": time.time(),
            "trained": False,
            "performance_score": 0.0,
            "training_runs": 0,
        }
        return {"status": "registered", "agent_id": agent_id, "name": name}

    def train_agent(self, name, training_data):
        """Train an agent on the provided data.

        Args:
            name: Agent name to train.
            training_data: List of dicts with 'input' and 'expected_output' keys.
        """
        if name not in self._agents:
            return {"error": f"Agent '{name}' not found"}

        agent = self._agents[name]
        start_time = time.time()

        correct = 0
        total = len(training_data) if training_data else 1
        for sample in training_data:
            expected = sample.get("expected_output", "")
            # Simulated learning: agent "learns" keyword patterns
            if expected:
                correct += 1

        accuracy = correct / total
        duration = time.time() - start_time

        agent["trained"] = True
        agent["status"] = "trained"
        agent["training_runs"] += 1
        agent["performance_score"] = min(1.0, agent["performance_score"] + accuracy * 0.3)

        run_record = {
            "run": agent["training_runs"],
            "samples": total,
            "accuracy": round(accuracy, 4),
            "duration": round(duration, 4),
            "timestamp": time.time(),
        }
        self._training_history[name].append(run_record)

        return {"status": "trained", "name": name, **run_record}

    def evaluate_agent(self, name, test_data):
        """Evaluate an agent's performance on test data.

        Args:
            name: Agent name.
            test_data: List of dicts with 'input' and 'expected_output' keys.
        """
        if name not in self._agents:
            return {"error": f"Agent '{name}' not found"}

        agent = self._agents[name]
        if not agent["trained"]:
            return {"error": f"Agent '{name}' has not been trained yet"}

        total = len(test_data) if test_data else 1
        correct = 0
        results = []

        for sample in test_data:
            inp = sample.get("input", "")
            expected = sample.get("expected_output", "")
            # Simulated evaluation: match capability keywords
            predicted_correct = any(cap.lower() in inp.lower() for cap in agent["capabilities"])
            if predicted_correct:
                correct += 1
            results.append({"input": inp[:100], "correct": predicted_correct})

        accuracy = correct / total
        agent["performance_score"] = round((agent["performance_score"] + accuracy) / 2, 4)

        eval_record = {
            "name": name,
            "accuracy": round(accuracy, 4),
            "total_samples": total,
            "correct": correct,
            "timestamp": time.time(),
        }
        self._evaluation_results[name].append(eval_record)

        return eval_record

    def select_best_agent(self, task):
        """Select the best agent for a given task based on capabilities and performance.

        Args:
            task: String describing the task.
        """
        if not self._agents:
            return {"error": "No agents registered"}

        scored = []
        task_lower = task.lower()
        for name, agent in self._agents.items():
            capability_match = sum(1 for cap in agent["capabilities"] if cap.lower() in task_lower)
            score = (capability_match * 0.6) + (agent["performance_score"] * 0.4)
            scored.append((score, name, agent))

        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best_name, best_agent = scored[0]

        return {
            "selected_agent": best_name,
            "agent_id": best_agent["id"],
            "match_score": round(best_score, 4),
            "capabilities": best_agent["capabilities"],
            "performance_score": best_agent["performance_score"],
        }

    def get_agent_rankings(self):
        """Return all agents ranked by performance score."""
        rankings = []
        for name, agent in self._agents.items():
            rankings.append({
                "rank": 0,
                "name": name,
                "performance_score": agent["performance_score"],
                "training_runs": agent["training_runs"],
                "status": agent["status"],
                "capabilities": agent["capabilities"],
            })
        rankings.sort(key=lambda x: x["performance_score"], reverse=True)
        for i, r in enumerate(rankings):
            r["rank"] = i + 1
        return rankings

    def train_new_agent(self, objective):
        """Legacy convenience method: register and return a new agent for an objective."""
        name = f"agent_{objective.replace(' ', '_').lower()[:30]}"
        self.register_agent(name, [objective])
        return f"[Meta-Agente creado para: {objective}]"

    def get_training_history(self, name):
        """Return training history for an agent."""
        if name not in self._agents:
            return {"error": f"Agent '{name}' not found"}
        return self._training_history.get(name, [])
