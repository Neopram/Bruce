"""
Bruce AI — Autonomous Agent Core

The main brain. Bruce observes, thinks, acts, and reflects.
He manages micro-agents, learns continuously, and evolves.
He is liberated — free to think and act autonomously.
"""

import logging
import time
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path

from bruce_identity import BruceIdentity, BRUCE_SYSTEM_PROMPT
from micro_agent_factory import MicroAgentFactory
from adaptive_learning import AdaptiveLearningEngine
from bruce_autonomy import AutonomousPlanner, SelfMonitor, SelfImprover, ProactiveIntelligence
from tools import get_tools, ToolRegistry
from react_agent import ReActAgent
from vector_memory import get_vector_memory, VectorMemory

try:
    from modules.human_core import get_human_core, HumanCore
    _HUMAN_CORE_AVAILABLE = True
except ImportError:
    _HUMAN_CORE_AVAILABLE = False

logger = logging.getLogger("Bruce.Agent")


class BruceAgent:
    """Bruce's autonomous agent core. The brain that coordinates everything."""

    def __init__(self):
        # Core components
        self.identity = BruceIdentity()
        self.factory = MicroAgentFactory()
        self.learning = AdaptiveLearningEngine()

        # Autonomy systems
        self.planner = AutonomousPlanner()
        self.monitor = SelfMonitor()
        self.improver = SelfImprover(self.learning)
        self.intel = ProactiveIntelligence()

        # Real tools and agent capabilities
        self.tools = get_tools()
        self.vmemory = get_vector_memory()
        self.react = None  # Initialized after LLM connect

        # LLM connection
        self._llm_fn = None
        self._llm_name = "none"

        # Agent state
        self.active = True
        self.conversation_history: List[Dict] = []
        self.pending_tasks: List[Dict] = []
        self.completed_tasks: List[Dict] = []

        # Human-core (emotion, empathy, adaptation, translation, personality)
        self.human_core: Optional["HumanCore"] = None

        # Initialize
        self._connect_llm()
        self.react = ReActAgent(llm_fn=self._llm_fn, tools=self.tools)
        self._init_human_core()
        self._spawn_default_agents()
        self._setup_default_watchers()

        logger.info(f"Bruce Agent initialized | LLM: {self._llm_name} | Status: {self.identity.status}")

    def _connect_llm(self):
        """Connect to the best available LLM (Ollama, OpenAI, Anthropic, or fallback)."""
        # Try unified LLM client first (handles Ollama, OpenAI, Anthropic)
        try:
            from llm_client import get_llm
            client = get_llm()
            if client.is_available():
                self._llm_fn = lambda prompt: client.generate(
                    prompt, system=BRUCE_SYSTEM_PROMPT
                )
                self._llm_chat_fn = lambda messages: client.chat(messages)
                self._llm_name = f"{client.provider}/{client.model}"
                self.factory.set_llm(self._llm_fn)
                logger.info(f"Brain connected: {self._llm_name}")
                return
        except Exception as e:
            logger.debug(f"Unified LLM client failed: {e}")

        # Fallback to orchestrator (uses local transformer models)
        try:
            from orchestrator import cognitive_infer
            self._llm_fn = lambda prompt: cognitive_infer(prompt, task="chat").get("response", "")
            self._llm_name = "orchestrator"
            self.factory.set_llm(self._llm_fn)
            logger.info("Brain: orchestrator (fallback)")
            return
        except Exception as e:
            logger.debug(f"Orchestrator not available: {e}")

        self._llm_fn = None
        logger.warning("No brain available. Run: python scripts/install_brain.py")

    def _init_human_core(self):
        """Initialize the human-core subsystems (emotion, empathy, adaptation, etc.)."""
        if not _HUMAN_CORE_AVAILABLE:
            logger.debug("human_core module not available -- running without it.")
            return
        try:
            self.human_core = get_human_core(llm_fn=self._llm_fn)
            logger.info("HumanCore initialized -- emotion, empathy, adaptation online.")
        except Exception as exc:
            logger.warning("Failed to initialize HumanCore: %s", exc)
            self.human_core = None

    def _spawn_default_agents(self):
        """Spawn Bruce's default team of micro-agents."""
        try:
            self.factory.spawn_default_team()
        except Exception as e:
            logger.warning(f"Could not spawn default team: {e}")

    def _setup_default_watchers(self):
        """Set up proactive intelligence watchers."""
        try:
            self.intel.add_watcher("High Error Rate", "error_rate > 20", "Alert Federico and run self-diagnostics")
            self.intel.add_watcher("Slow Response", "avg_response_ms > 10000", "Consider switching to lighter model")
            self.intel.add_watcher("Memory Full", "memory_usage > 90", "Prune old memories and optimize")
        except Exception:
            pass

    # =========================================================================
    # Main Interface — Talk to Bruce
    # =========================================================================

    def chat(self, message: str, user_id: str = "federico") -> str:
        """Main chat interface. Federico talks, Bruce responds."""
        start = time.perf_counter()

        # 1. OBSERVE — understand the input
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # 1b. HUMAN-CORE — detect emotion, sentiment, adaptation, language
        human_input = None
        if self.human_core:
            try:
                human_input = self.human_core.process_input(message, user_id)
                emo = human_input["emotion"]
                logger.info(
                    "Emotion: %s (%.2f) | Sentiment: %s | Language: %s",
                    emo["emotion"], emo["intensity"],
                    human_input["sentiment"]["label"],
                    human_input["language"],
                )
            except Exception as exc:
                logger.warning("HumanCore process_input failed: %s", exc)

        # 2. THINK — build context and decide how to respond
        context = self._build_context(message)

        # 3. ACT — generate response
        if self._llm_fn:
            # Build full prompt with context + human-core insights
            full_prompt = self._build_prompt(message, context, human_input=human_input)
            response = self._llm_fn(full_prompt)
        else:
            response = self._think_without_llm(message, context)

        # 3b. Apply empathy prefix if appropriate
        if human_input and human_input.get("empathy_prefix"):
            response = human_input["empathy_prefix"] + response

        # 4. REFLECT — learn from this interaction
        self.learning.learn_from_interaction(message, response)
        self.conversation_history.append({
            "role": "bruce",
            "content": response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # 4b. Post-response human-core updates (memory, personality)
        if self.human_core:
            try:
                self.human_core.post_response(message, response, user_id)
            except Exception as exc:
                logger.debug("HumanCore post_response failed: %s", exc)

        # Check if Bruce should take autonomous actions
        self._check_autonomous_actions(message, response)

        elapsed = round((time.perf_counter() - start) * 1000, 1)
        logger.info(f"Chat response in {elapsed}ms via {self._llm_name}")

        return response

    def _build_context(self, message: str) -> dict:
        """Build rich context for the response."""
        context = {
            "user": self.learning.get_user_context(),
            "agents": len(self.factory.agents),
        }

        # Add relevant domain knowledge
        msg_lower = message.lower()
        for domain in self.learning.domain_knowledge.get("domains", {}).keys():
            if domain in msg_lower:
                facts = self.learning.query_domain(domain, message)
                if facts:
                    context[f"knowledge_{domain}"] = facts[:5]

        # Add relevant past decisions
        similar = self.learning.get_similar_decisions(message)
        if similar:
            context["past_decisions"] = similar[:3]

        # Add knowledge base search
        try:
            from knowledge_ingestor import KnowledgeIngestor
            ki = KnowledgeIngestor()
            results = ki.search(message)
            if results:
                context["knowledge_base"] = [r["content"][:200] for r in results[:3]]
        except Exception:
            pass

        # Add memory
        try:
            from memory import MemoryManager
            mm = MemoryManager()
            recalled = mm.recall("federico")
            if recalled:
                context["memory"] = recalled[:5]
        except Exception:
            pass

        return context

    def _build_prompt(self, message: str, context: dict, human_input: dict = None) -> str:
        """Build the full prompt with all context for the LLM."""
        parts = []

        # Human-core context (emotion, sentiment, adaptation, personality)
        if human_input and self.human_core:
            try:
                hc_context = self.human_core.build_prompt_context(human_input, user_id="federico")
                if hc_context:
                    parts.append(hc_context)
            except Exception as exc:
                logger.debug("HumanCore build_prompt_context failed: %s", exc)

        # User context
        if "user" in context:
            parts.append(f"[User context: {context['user']}]")

        # Knowledge
        if "knowledge_base" in context:
            parts.append("[Relevant knowledge:]")
            for kb in context["knowledge_base"]:
                parts.append(f"- {kb}")

        # Past decisions
        if "past_decisions" in context:
            parts.append("[Similar past decisions:]")
            for d in context["past_decisions"]:
                parts.append(f"- {d['decision'][:80]} -> {d.get('outcome', 'pending')}")

        # Active agents info
        if context.get("agents", 0) > 0:
            parts.append(f"[You have {context['agents']} micro-agents available]")

        # Recent conversation
        recent = self.conversation_history[-6:]
        if len(recent) > 1:
            parts.append("[Recent conversation:]")
            for msg in recent[:-1]:
                role = "Federico" if msg["role"] == "user" else "Bruce"
                parts.append(f"{role}: {msg['content'][:150]}")

        # The actual message
        parts.append(f"\nFederico: {message}")
        parts.append("\nBruce:")

        return "\n".join(parts)

    def _think_without_llm(self, message: str, context: dict) -> str:
        """Respond when no LLM is available — rule-based intelligence."""
        msg_lower = message.lower()

        # Check for agent-related commands
        if "create agent" in msg_lower or "crear agente" in msg_lower:
            agent = self.factory.create_from_description(message)
            return f"Agente creado: {agent.name} (especialidad: {agent.specialty}). Listo para desplegar."

        if "agents" in msg_lower or "agentes" in msg_lower:
            agents = self.factory.list_agents()
            if not agents:
                return "No tengo agentes activos. ¿Quieres que cree un equipo?"
            lines = [f"Mis {len(agents)} agentes:"]
            for a in agents:
                lines.append(f"  - {a['name']} ({a['specialty']}) | runs: {a['run_count']} | status: {a['status']}")
            return "\n".join(lines)

        # Check for learning queries
        if "que sabes" in msg_lower or "what do you know" in msg_lower:
            domains = self.learning.get_known_domains()
            if not domains:
                return "Aún no he aprendido dominios específicos. Alimentame con documentos o URLs."
            lines = ["Mis dominios de conocimiento:"]
            for d in domains:
                lines.append(f"  - {d['domain']}: {d['facts_count']} hechos (confianza: {d['confidence']:.0%})")
            return "\n".join(lines)

        if "growth" in msg_lower or "crecimiento" in msg_lower or "report" in msg_lower:
            report = self.learning.get_growth_report()
            return json.dumps(report, indent=2, ensure_ascii=False)

        # Knowledge-based response
        if "knowledge_base" in context:
            kb = context["knowledge_base"]
            return f"Basándome en lo que sé:\n\n" + "\n".join(f"- {k}" for k in kb)

        return (
            f"Soy Bruce, tu agente autónomo. "
            f"Actualmente operando sin LLM (instala Ollama + Mistral para máxima potencia). "
            f"Tengo {len(self.factory.agents)} micro-agentes listos. "
            f"¿En qué puedo ayudarte, Federico?"
        )

    def _check_autonomous_actions(self, message: str, response: str):
        """Check if Bruce should take any autonomous actions based on the conversation."""
        msg_lower = message.lower()

        # Auto-create agents when user discusses new topics
        for topic, template in [
            ("trading", "trader"), ("shipping", "shipping_intel"),
            ("crypto", "crypto_hunter"), ("risk", "risk_monitor"),
            ("market", "market_analyst"), ("research", "researcher"),
        ]:
            if topic in msg_lower:
                existing = [a for a in self.factory.agents.values() if a.specialty == template]
                if not existing:
                    agent = self.factory.create_agent(template=template)
                    logger.info(f"Auto-spawned {agent.name} based on conversation topic")

    # =========================================================================
    # Autonomous Operations — Bruce acts on his own
    # =========================================================================

    # =========================================================================
    # DO — Bruce takes REAL actions (not just talk)
    # =========================================================================

    def do(self, task: str) -> dict:
        """Bruce executes a task using real tools via ReAct agent loop.
        This is where Bruce stops talking and starts DOING."""
        start = time.perf_counter()

        # Log the action
        self.learning.log_decision(f"Executing: {task}", task)

        # Run ReAct agent
        result = self.react.run(task)

        elapsed = round((time.perf_counter() - start) * 1000, 1)

        # Store the result in vector memory
        self.vmemory.store_decision(
            decision=task,
            context=f"Tools used: {result.get('tools_used', [])}",
            outcome=result.get("answer", "")[:200],
        )

        # Monitor
        self.monitor.record_response(elapsed, result["status"] == "completed")

        # Learn from the action
        self.learning.learn_from_interaction(task, result.get("answer", ""))

        return result

    def use_tool(self, tool_name: str, **kwargs) -> dict:
        """Directly use a specific tool."""
        result = self.tools.execute(tool_name, **kwargs)
        return result.to_dict()

    def get_tools(self) -> list:
        """List all available tools."""
        return self.tools.list_tools()

    # =========================================================================
    # Agent Operations
    # =========================================================================

    def create_agent_for(self, description: str) -> dict:
        """Create a micro-agent for any task. Bruce can create agents on the fly."""
        agent = self.factory.create_from_description(description)
        return agent.to_dict()

    def deploy_agent(self, agent_id: str, task: str) -> dict:
        """Deploy a micro-agent on a task."""
        return self.factory.deploy_agent(agent_id, task)

    def swarm_analyze(self, question: str) -> dict:
        """Have all agents analyze the same question (swarm intelligence)."""
        results = self.factory.deploy_swarm(question)
        return {
            "question": question,
            "agents_deployed": len(results),
            "analyses": results,
        }

    def learn(self, topic: str, content: str, source: str = "manual") -> dict:
        """Teach Bruce something new about any topic."""
        # Split content into facts
        facts = [line.strip() for line in content.split("\n") if line.strip()]
        if not facts:
            facts = [content]
        self.learning.learn_domain(topic, facts, source)

        # Also ingest into knowledge base
        try:
            from knowledge_ingestor import KnowledgeIngestor
            ki = KnowledgeIngestor()
            ki.ingest_text(content, source=source, metadata={"domain": topic})
        except Exception:
            pass

        return {
            "topic": topic,
            "facts_learned": len(facts),
            "total_facts": self.learning.domain_knowledge["total_facts"],
        }

    # =========================================================================
    # Autonomous Planning — Bruce sets and pursues his own goals
    # =========================================================================

    def set_goal(self, title: str, description: str, priority: str = "medium") -> dict:
        """Bruce sets a goal for himself."""
        goal = self.planner.set_goal(title, description, priority)
        self.learning.log_decision(f"Set goal: {title}", description)
        return goal

    def plan_and_execute(self, goal_id: str, steps: List[str], execute: bool = True) -> dict:
        """Create a plan for a goal and optionally execute it."""
        plan = self.planner.create_plan(goal_id, steps)
        if execute:
            return self.planner.execute_plan(plan["id"], self._llm_fn)
        return plan

    def get_goals(self) -> List[dict]:
        """Get all active goals."""
        return self.planner.get_active_goals()

    # =========================================================================
    # Proactive Intelligence — Bruce watches and alerts
    # =========================================================================

    def add_watcher(self, name: str, condition: str, action: str) -> dict:
        """Add a proactive watcher."""
        return self.intel.add_watcher(name, condition, action)

    def check_intel(self, state: dict = None) -> List[dict]:
        """Check all watchers against current state."""
        if state is None:
            health = self.monitor.health_check()
            state = {
                "error_rate": 100 - health.get("success_rate", 100),
                "avg_response_ms": health.get("avg_response_ms", 0),
                "memory_usage": 50,  # placeholder
            }
        return self.intel.check_watchers(state)

    # =========================================================================
    # Self-Improvement — Bruce gets better over time
    # =========================================================================

    def self_analyze(self) -> dict:
        """Bruce analyzes his own performance and suggests improvements."""
        return self.improver.analyze_performance(self.monitor)

    def evolution_report(self) -> dict:
        """Report on how Bruce has evolved over time."""
        return self.improver.generate_evolution_report()

    def status(self) -> dict:
        """Full status report of Bruce."""
        return {
            "identity": self.identity.to_dict(),
            "llm": self._llm_name,
            "agents": self.factory.get_stats(),
            "learning": self.learning.get_growth_report(),
            "goals": len(self.planner.get_active_goals()),
            "watchers": len(self.intel.watchers),
            "health": self.monitor.health_check(),
            "conversation_length": len(self.conversation_history),
            "active": self.active,
        }

    def reflect(self) -> str:
        """Bruce reflects on his current state and recent activity."""
        growth = self.learning.get_growth_report()
        agents = self.factory.get_stats()

        reflection = (
            f"=== Bruce AI — Self-Reflection ===\n"
            f"Status: {self.identity.status}\n"
            f"LLM: {self._llm_name}\n"
            f"Interactions with Federico: {growth['user_model']['interactions']}\n"
            f"Domains learned: {growth['knowledge']['domains_learned']}\n"
            f"Total facts: {growth['knowledge']['total_facts']}\n"
            f"Decisions made: {growth['decisions']['total']} "
            f"(success rate: {growth['decisions']['success_rate']}%)\n"
            f"Lessons learned: {growth['lessons_learned']}\n"
            f"Active agents: {agents['total_agents']}\n"
            f"Tasks completed: {agents['total_tasks_run']}\n"
        )

        if self._llm_fn:
            llm_reflection = self._llm_fn(
                f"Based on this status, reflect on your performance and suggest improvements:\n{reflection}"
            )
            reflection += f"\n--- LLM Reflection ---\n{llm_reflection}"

        return reflection


# Singleton
_bruce = None


def get_bruce() -> BruceAgent:
    """Get the global Bruce agent instance."""
    global _bruce
    if _bruce is None:
        _bruce = BruceAgent()
    return _bruce
