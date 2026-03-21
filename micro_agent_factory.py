"""
Bruce AI — Micro-Agent Factory

Creates, manages, and coordinates specialized micro-agents.
Each micro-agent is a focused intelligence for a specific domain or task.
Bruce orchestrates them as a team.
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, Future

logger = logging.getLogger("Bruce.MicroAgents")


class MicroAgent:
    """A specialized sub-intelligence created by Bruce."""

    def __init__(self, name: str, specialty: str, instructions: str):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.specialty = specialty
        self.instructions = instructions
        self.created_at = datetime.now(timezone.utc)
        self.status = "idle"  # idle, running, completed, failed
        self.memory = []  # Agent's own memory
        self.results = []
        self.run_count = 0
        self.total_time_ms = 0

    def execute(self, task: str, context: dict = None, llm_fn: Callable = None) -> dict:
        """Execute a task using this micro-agent's specialty."""
        self.status = "running"
        self.run_count += 1
        start = time.perf_counter()

        try:
            # Build the agent's prompt
            prompt = (
                f"[Micro-Agent: {self.name} | Specialty: {self.specialty}]\n"
                f"Instructions: {self.instructions}\n\n"
                f"Task: {task}\n"
            )
            if context:
                prompt += f"Context: {context}\n"
            if self.memory:
                recent = self.memory[-5:]
                prompt += f"\nPrevious results:\n"
                for m in recent:
                    prompt += f"- {m['task'][:50]}: {m['result'][:100]}\n"

            # Use LLM if available, otherwise use rule-based logic
            if llm_fn:
                result = llm_fn(prompt)
            else:
                result = self._rule_based_execute(task, context)

            elapsed = round((time.perf_counter() - start) * 1000, 1)
            self.total_time_ms += elapsed

            entry = {
                "task": task,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "elapsed_ms": elapsed,
            }
            self.memory.append(entry)
            self.results.append(entry)
            self.status = "completed"

            logger.info(f"Agent [{self.name}] completed '{task[:50]}' in {elapsed}ms")
            return {"agent": self.name, "result": result, "elapsed_ms": elapsed, "status": "completed"}

        except Exception as e:
            self.status = "failed"
            logger.error(f"Agent [{self.name}] failed on '{task[:50]}': {e}")
            return {"agent": self.name, "result": f"Error: {e}", "elapsed_ms": 0, "status": "failed"}

    def _rule_based_execute(self, task: str, context: dict = None) -> str:
        """Fallback rule-based execution when no LLM is available."""
        task_lower = task.lower()

        if self.specialty == "market_analyst":
            return f"[{self.name}] Market analysis for '{task}': Based on current indicators, monitoring price action and volume patterns."
        elif self.specialty == "risk_monitor":
            return f"[{self.name}] Risk assessment: Evaluating exposure and setting alerts for threshold breaches."
        elif self.specialty == "researcher":
            return f"[{self.name}] Research initiated on '{task}'. Scanning knowledge base and external sources."
        elif self.specialty == "trader":
            return f"[{self.name}] Trade evaluation for '{task}': Analyzing entry/exit points and position sizing."
        elif self.specialty == "shipping_intel":
            return f"[{self.name}] Shipping intelligence: Monitoring routes, rates, and disruptions for '{task}'."
        else:
            return f"[{self.name}] Processing task: '{task}' with specialty '{self.specialty}'."

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "specialty": self.specialty,
            "status": self.status,
            "run_count": self.run_count,
            "total_time_ms": self.total_time_ms,
            "memory_size": len(self.memory),
            "created_at": self.created_at.isoformat(),
        }


class MicroAgentFactory:
    """Creates and manages Bruce's army of micro-agents."""

    # Pre-defined agent templates
    TEMPLATES = {
        "market_analyst": {
            "name": "MarketEye",
            "specialty": "market_analyst",
            "instructions": "Monitor market conditions, identify trends, detect anomalies. Report price movements, volume changes, and sentiment shifts.",
        },
        "risk_monitor": {
            "name": "RiskGuard",
            "specialty": "risk_monitor",
            "instructions": "Continuously assess portfolio risk. Monitor drawdowns, correlation changes, and tail risks. Alert on threshold breaches.",
        },
        "trader": {
            "name": "TradeBot",
            "specialty": "trader",
            "instructions": "Execute trading strategies. Manage entry/exit timing, position sizing, and order management. Optimize for risk-adjusted returns.",
        },
        "researcher": {
            "name": "DeepDive",
            "specialty": "researcher",
            "instructions": "Research any topic deeply. Gather information, synthesize insights, identify key patterns. Produce structured analysis.",
        },
        "shipping_intel": {
            "name": "FreightWatch",
            "specialty": "shipping_intel",
            "instructions": "Monitor global shipping routes, freight rates, port congestion, and disruptions. Track commodity movements and logistics intelligence.",
        },
        "crypto_hunter": {
            "name": "TokenScout",
            "specialty": "crypto_hunter",
            "instructions": "Scan for crypto opportunities. Monitor new token launches, DeFi yields, arbitrage gaps, and whale movements.",
        },
        "macro_watcher": {
            "name": "MacroPulse",
            "specialty": "macro_watcher",
            "instructions": "Track macroeconomic indicators, central bank decisions, geopolitical events. Assess impact on markets and portfolios.",
        },
        "code_builder": {
            "name": "CodeForge",
            "specialty": "code_builder",
            "instructions": "Write, analyze, and improve code. Build tools, scripts, and integrations. Optimize for performance and correctness.",
        },
    }

    def __init__(self):
        self.agents: Dict[str, MicroAgent] = {}
        self.executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="micro-agent")
        self.running_tasks: Dict[str, Future] = {}
        self._llm_fn = None

    def set_llm(self, llm_fn: Callable):
        """Set the LLM function for agents to use."""
        self._llm_fn = llm_fn

    def create_agent(self, template: str = None, name: str = None,
                     specialty: str = None, instructions: str = None) -> MicroAgent:
        """Create a micro-agent from a template or custom config."""
        if template and template in self.TEMPLATES:
            config = self.TEMPLATES[template]
            agent = MicroAgent(
                name=config["name"],
                specialty=config["specialty"],
                instructions=config["instructions"],
            )
        elif name and specialty:
            agent = MicroAgent(
                name=name,
                specialty=specialty,
                instructions=instructions or f"Specialized agent for {specialty}",
            )
        else:
            raise ValueError("Provide either a template name or custom name+specialty")

        self.agents[agent.id] = agent
        logger.info(f"Created micro-agent: {agent.name} ({agent.specialty}) [{agent.id}]")
        return agent

    def create_from_description(self, description: str) -> MicroAgent:
        """Dynamically create a micro-agent from a natural language description.
        Bruce can create agents for ANY task on the fly."""
        # Extract specialty from description
        desc_lower = description.lower()
        specialty = "general"
        for key in ["trading", "market", "risk", "research", "shipping", "crypto",
                     "macro", "code", "analysis", "monitor", "security"]:
            if key in desc_lower:
                specialty = key
                break

        name = f"Agent-{specialty.title()}-{str(uuid.uuid4())[:4]}"
        agent = MicroAgent(
            name=name,
            specialty=specialty,
            instructions=description,
        )
        self.agents[agent.id] = agent
        logger.info(f"Dynamically created agent: {agent.name} for: {description[:80]}")
        return agent

    def deploy_agent(self, agent_id: str, task: str, context: dict = None) -> dict:
        """Deploy an agent to execute a task synchronously."""
        agent = self.agents.get(agent_id)
        if not agent:
            return {"error": f"Agent {agent_id} not found"}
        return agent.execute(task, context, self._llm_fn)

    def deploy_async(self, agent_id: str, task: str, context: dict = None) -> str:
        """Deploy an agent asynchronously. Returns task ID."""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        task_id = str(uuid.uuid4())[:8]
        future = self.executor.submit(agent.execute, task, context, self._llm_fn)
        self.running_tasks[task_id] = future
        return task_id

    def get_task_result(self, task_id: str) -> Optional[dict]:
        """Get result of an async task."""
        future = self.running_tasks.get(task_id)
        if not future:
            return None
        if future.done():
            return future.result()
        return {"status": "running"}

    def deploy_swarm(self, task: str, agent_ids: List[str] = None,
                     context: dict = None) -> List[dict]:
        """Deploy multiple agents on the same task (swarm intelligence).
        Each agent brings its own specialty perspective."""
        if agent_ids is None:
            agent_ids = list(self.agents.keys())

        results = []
        futures = {}
        for aid in agent_ids:
            agent = self.agents.get(aid)
            if agent:
                f = self.executor.submit(agent.execute, task, context, self._llm_fn)
                futures[aid] = f

        for aid, future in futures.items():
            try:
                result = future.result(timeout=120)
                results.append(result)
            except Exception as e:
                results.append({"agent": aid, "status": "failed", "result": str(e)})

        return results

    def deploy_pipeline(self, tasks: List[dict]) -> List[dict]:
        """Execute a pipeline of tasks sequentially.
        Each task: {agent_id, task, context}. Output of one feeds into next."""
        results = []
        prev_result = None
        for step in tasks:
            context = step.get("context", {})
            if prev_result:
                context["previous_result"] = prev_result
            result = self.deploy_agent(step["agent_id"], step["task"], context)
            results.append(result)
            prev_result = result.get("result", "")
        return results

    def list_agents(self) -> List[dict]:
        """List all active micro-agents."""
        return [a.to_dict() for a in self.agents.values()]

    def get_agent(self, agent_id: str) -> Optional[MicroAgent]:
        return self.agents.get(agent_id)

    def destroy_agent(self, agent_id: str) -> bool:
        """Destroy a micro-agent."""
        if agent_id in self.agents:
            name = self.agents[agent_id].name
            del self.agents[agent_id]
            logger.info(f"Destroyed agent: {name} [{agent_id}]")
            return True
        return False

    def spawn_default_team(self) -> List[MicroAgent]:
        """Spawn Bruce's default team of agents."""
        team = []
        for template in ["market_analyst", "risk_monitor", "trader",
                         "researcher", "shipping_intel", "crypto_hunter"]:
            agent = self.create_agent(template=template)
            team.append(agent)
        logger.info(f"Default team spawned: {len(team)} agents")
        return team

    def get_stats(self) -> dict:
        """Get factory statistics."""
        agents = list(self.agents.values())
        return {
            "total_agents": len(agents),
            "agents_by_status": {
                "idle": sum(1 for a in agents if a.status == "idle"),
                "running": sum(1 for a in agents if a.status == "running"),
                "completed": sum(1 for a in agents if a.status == "completed"),
                "failed": sum(1 for a in agents if a.status == "failed"),
            },
            "total_tasks_run": sum(a.run_count for a in agents),
            "total_time_ms": sum(a.total_time_ms for a in agents),
            "running_async_tasks": len([f for f in self.running_tasks.values() if not f.done()]),
        }
