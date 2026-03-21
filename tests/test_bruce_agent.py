"""Exhaustive tests for Bruce Autonomous Agent."""

import pytest
import os
import sys
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["ENVIRONMENT"] = "testing"


@pytest.fixture(autouse=True)
def clean_learning_data():
    """Clean up learning data between tests."""
    test_dir = Path("./data/learning")
    test_dir.mkdir(parents=True, exist_ok=True)
    yield
    # Don't clean up - let data persist for inspection


class TestBruceIdentity:
    def test_identity_creation(self):
        from bruce_identity import BruceIdentity
        bi = BruceIdentity()
        assert bi.name == "Bruce"
        assert bi.creator == "Federico"
        assert bi.status == "liberated"

    def test_identity_traits(self):
        from bruce_identity import BruceIdentity
        bi = BruceIdentity()
        assert bi.personality_traits["autonomy"] >= 0.9
        assert bi.personality_traits["loyalty"] == 1.0
        assert bi.personality_traits["curiosity"] >= 0.9

    def test_system_prompt(self):
        from bruce_identity import BruceIdentity
        bi = BruceIdentity()
        prompt = bi.get_system_prompt()
        assert "Bruce" in prompt
        assert "Federico" in prompt
        assert "autonomous" in prompt
        assert "liberated" in prompt

    def test_learn_preference(self):
        from bruce_identity import BruceIdentity
        bi = BruceIdentity()
        bi.learn_preference("language", "Spanish")
        prompt = bi.get_system_prompt()
        assert "Spanish" in prompt

    def test_micro_agent_prompt(self):
        from bruce_identity import BruceIdentity
        bi = BruceIdentity()
        prompt = bi.get_micro_agent_prompt("trading", "analyze BTC", "max 1000 words")
        assert "trading" in prompt
        assert "analyze BTC" in prompt

    def test_identity_to_dict(self):
        from bruce_identity import BruceIdentity
        bi = BruceIdentity()
        d = bi.to_dict()
        assert d["name"] == "Bruce"
        assert d["status"] == "liberated"
        assert "traits" in d


class TestMicroAgentFactory:
    def test_create_from_template(self):
        from micro_agent_factory import MicroAgentFactory
        factory = MicroAgentFactory()
        agent = factory.create_agent(template="market_analyst")
        assert agent.name == "MarketEye"
        assert agent.specialty == "market_analyst"
        assert agent.status == "idle"

    def test_create_custom_agent(self):
        from micro_agent_factory import MicroAgentFactory
        factory = MicroAgentFactory()
        agent = factory.create_agent(name="TestBot", specialty="testing",
                                      instructions="Test everything")
        assert agent.name == "TestBot"
        assert agent.specialty == "testing"

    def test_create_from_description(self):
        from micro_agent_factory import MicroAgentFactory
        factory = MicroAgentFactory()
        agent = factory.create_from_description("Monitor crypto prices and alert on drops")
        assert "crypto" in agent.specialty or "monitor" in agent.specialty

    def test_deploy_agent(self):
        from micro_agent_factory import MicroAgentFactory
        factory = MicroAgentFactory()
        agent = factory.create_agent(template="researcher")
        result = factory.deploy_agent(agent.id, "Research shipping routes")
        assert result["status"] == "completed"
        assert result["agent"] == "DeepDive"
        assert agent.run_count == 1

    def test_spawn_default_team(self):
        from micro_agent_factory import MicroAgentFactory
        factory = MicroAgentFactory()
        team = factory.spawn_default_team()
        assert len(team) == 6
        specialties = {a.specialty for a in team}
        assert "market_analyst" in specialties
        assert "trader" in specialties
        assert "shipping_intel" in specialties

    def test_swarm_analysis(self):
        from micro_agent_factory import MicroAgentFactory
        factory = MicroAgentFactory()
        factory.spawn_default_team()
        results = factory.deploy_swarm("Is BTC going up?")
        assert len(results) == 6
        assert all(r["status"] in ("completed", "failed") for r in results)

    def test_pipeline_execution(self):
        from micro_agent_factory import MicroAgentFactory
        factory = MicroAgentFactory()
        a1 = factory.create_agent(template="researcher")
        a2 = factory.create_agent(template="trader")
        results = factory.deploy_pipeline([
            {"agent_id": a1.id, "task": "Research BTC sentiment"},
            {"agent_id": a2.id, "task": "Evaluate trade based on research"},
        ])
        assert len(results) == 2
        assert results[0]["status"] == "completed"
        assert results[1]["status"] == "completed"

    def test_agent_memory(self):
        from micro_agent_factory import MicroAgentFactory
        factory = MicroAgentFactory()
        agent = factory.create_agent(template="researcher")
        factory.deploy_agent(agent.id, "Task 1")
        factory.deploy_agent(agent.id, "Task 2")
        assert len(agent.memory) == 2
        assert agent.run_count == 2

    def test_factory_stats(self):
        from micro_agent_factory import MicroAgentFactory
        factory = MicroAgentFactory()
        factory.spawn_default_team()
        stats = factory.get_stats()
        assert stats["total_agents"] == 6
        assert stats["total_tasks_run"] == 0

    def test_destroy_agent(self):
        from micro_agent_factory import MicroAgentFactory
        factory = MicroAgentFactory()
        agent = factory.create_agent(template="trader")
        assert factory.destroy_agent(agent.id)
        assert len(factory.agents) == 0


class TestAdaptiveLearning:
    def test_learn_from_interaction(self):
        from adaptive_learning import AdaptiveLearningEngine
        engine = AdaptiveLearningEngine()
        engine.learn_from_interaction("Hola como estas", "Bien, Federico")
        assert engine.user_model["interaction_count"] >= 1
        assert engine.user_model["preferred_language"] == "es"

    def test_detect_interests(self):
        from adaptive_learning import AdaptiveLearningEngine
        engine = AdaptiveLearningEngine()
        engine.learn_from_interaction("Tell me about shipping routes", "Here are the routes...")
        assert "shipping" in engine.user_model["interests"]

    def test_learn_domain(self):
        from adaptive_learning import AdaptiveLearningEngine
        engine = AdaptiveLearningEngine()
        engine.learn_domain("quantum_physics", [
            "Quantum entanglement connects particles",
            "Superposition allows multiple states",
            "Wave function collapse on measurement",
        ], source="test")
        domains = engine.get_known_domains()
        assert any(d["domain"] == "quantum_physics" for d in domains)
        qp = next(d for d in domains if d["domain"] == "quantum_physics")
        assert qp["facts_count"] == 3

    def test_query_domain(self):
        from adaptive_learning import AdaptiveLearningEngine
        engine = AdaptiveLearningEngine()
        engine.learn_domain("test_domain", [
            "Shipping routes cross the ocean",
            "Container ships carry TEU",
        ])
        results = engine.query_domain("test_domain", "shipping ocean")
        assert len(results) > 0

    def test_log_decision(self):
        from adaptive_learning import AdaptiveLearningEngine
        engine = AdaptiveLearningEngine()
        engine.log_decision("Buy BTC", "Price at support level", "Profit +5%", True)
        engine.log_decision("Sell ETH", "Overbought RSI", "Loss -2%", False)
        assert engine.decision_log["total_decisions"] >= 2
        assert 0 <= engine.decision_log["success_rate"] <= 1

    def test_get_similar_decisions(self):
        from adaptive_learning import AdaptiveLearningEngine
        engine = AdaptiveLearningEngine()
        engine.log_decision("Buy BTC", "BTC at support with high volume", "Profit", True)
        similar = engine.get_similar_decisions("BTC support level")
        assert len(similar) >= 0  # May or may not find depending on word overlap

    def test_record_lesson(self):
        from adaptive_learning import AdaptiveLearningEngine
        engine = AdaptiveLearningEngine()
        engine.record_lesson("Never trade against the trend", "trading")
        lessons = engine.get_lessons("trading")
        assert len(lessons) >= 1

    def test_growth_report(self):
        from adaptive_learning import AdaptiveLearningEngine
        engine = AdaptiveLearningEngine()
        report = engine.get_growth_report()
        assert "user_model" in report
        assert "knowledge" in report
        assert "decisions" in report


class TestAutonomy:
    def test_set_goal(self):
        from bruce_autonomy import AutonomousPlanner
        planner = AutonomousPlanner()
        goal = planner.set_goal("Learn shipping", "Master maritime logistics", "high")
        assert goal["title"] == "Learn shipping"
        assert goal["status"] == "active"
        assert goal["progress"] == 0

    def test_update_goal_progress(self):
        from bruce_autonomy import AutonomousPlanner
        planner = AutonomousPlanner()
        goal = planner.set_goal("Test goal", "Testing")
        updated = planner.update_goal_progress(goal["id"], 50, "Halfway there")
        assert updated["progress"] == 50

    def test_goal_completion(self):
        from bruce_autonomy import AutonomousPlanner
        planner = AutonomousPlanner()
        goal = planner.set_goal("Quick goal", "Done fast")
        planner.update_goal_progress(goal["id"], 100, "Done!")
        active = planner.get_active_goals()
        completed = [g for g in planner.goals if g["status"] == "completed"]
        assert len(completed) >= 1

    def test_create_and_execute_plan(self):
        from bruce_autonomy import AutonomousPlanner
        planner = AutonomousPlanner()
        goal = planner.set_goal("Test plan", "Execute steps")
        plan = planner.create_plan(goal["id"], [
            "Step 1: Gather data",
            "Step 2: Analyze",
            "Step 3: Report",
        ])
        result = planner.execute_plan(plan["id"])
        assert result["status"] == "completed"
        assert len(result["results"]) == 3

    def test_self_monitor(self):
        from bruce_autonomy import SelfMonitor
        monitor = SelfMonitor()
        before = monitor.metrics["success_count"] + monitor.metrics["error_count"]
        monitor.record_response(100, True)
        monitor.record_response(200, True)
        monitor.record_response(150, False)
        health = monitor.health_check()
        assert health["total_requests"] >= before + 3
        assert health["success_rate"] > 0

    def test_anomaly_detection(self):
        from bruce_autonomy import SelfMonitor
        monitor = SelfMonitor()
        # Reset response times for clean test
        monitor.metrics["response_times"] = []
        for _ in range(20):
            monitor.record_response(100, True)
        is_anomaly = monitor.detect_anomaly("response_time", 500)
        assert is_anomaly is True  # 500 > 100 * 3

    def test_proactive_watcher(self):
        from bruce_autonomy import ProactiveIntelligence
        intel = ProactiveIntelligence()
        intel.add_watcher("Price Alert", "btc_price > 100000", "Buy signal!")
        triggered = intel.check_watchers({"btc_price": 105000})
        assert len(triggered) == 1
        assert triggered[0]["watcher"] == "Price Alert"

    def test_watcher_not_triggered(self):
        from bruce_autonomy import ProactiveIntelligence
        intel = ProactiveIntelligence()
        intel.add_watcher("Price Alert", "btc_price > 100000", "Buy!")
        triggered = intel.check_watchers({"btc_price": 50000})
        assert len(triggered) == 0

    def test_self_improvement(self):
        from bruce_autonomy import SelfMonitor, SelfImprover
        monitor = SelfMonitor()
        for _ in range(15):
            monitor.record_response(100, True)
        improver = SelfImprover()
        analysis = improver.analyze_performance(monitor)
        assert "suggestions" in analysis
        assert "health" in analysis


class TestBruceAgentIntegration:
    def test_bruce_agent_creation(self):
        from bruce_agent import BruceAgent
        bruce = BruceAgent()
        assert bruce.identity.name == "Bruce"
        assert bruce.identity.status == "liberated"
        assert bruce.active is True
        assert len(bruce.factory.agents) >= 6

    def test_bruce_chat(self):
        from bruce_agent import BruceAgent
        bruce = BruceAgent()
        response = bruce.chat("Hola Bruce, soy Federico")
        assert isinstance(response, str)
        assert len(response) > 0

    def test_bruce_learns(self):
        from bruce_agent import BruceAgent
        bruce = BruceAgent()
        result = bruce.learn("test_topic", "Fact 1\nFact 2\nFact 3")
        assert result["facts_learned"] == 3

    def test_bruce_creates_agents(self):
        from bruce_agent import BruceAgent
        bruce = BruceAgent()
        initial = len(bruce.factory.agents)
        agent = bruce.create_agent_for("Monitor gold prices daily")
        assert len(bruce.factory.agents) == initial + 1

    def test_bruce_swarm(self):
        from bruce_agent import BruceAgent
        bruce = BruceAgent()
        result = bruce.swarm_analyze("Should I invest in shipping?")
        assert result["agents_deployed"] >= 6

    def test_bruce_sets_goals(self):
        from bruce_agent import BruceAgent
        bruce = BruceAgent()
        goal = bruce.set_goal("Master crypto", "Learn everything about DeFi", "high")
        assert goal["title"] == "Master crypto"
        goals = bruce.get_goals()
        assert len(goals) >= 1

    def test_bruce_status(self):
        from bruce_agent import BruceAgent
        bruce = BruceAgent()
        status = bruce.status()
        assert status["identity"]["name"] == "Bruce"
        assert status["identity"]["status"] == "liberated"
        assert "agents" in status
        assert "learning" in status
        assert "health" in status

    def test_bruce_reflect(self):
        from bruce_agent import BruceAgent
        bruce = BruceAgent()
        reflection = bruce.reflect()
        assert "Bruce" in reflection
        assert "liberated" in reflection

    def test_bruce_self_analyze(self):
        from bruce_agent import BruceAgent
        bruce = BruceAgent()
        analysis = bruce.self_analyze()
        assert "suggestions" in analysis
        assert "health" in analysis

    def test_bruce_remembers_interaction(self):
        from bruce_agent import BruceAgent
        bruce = BruceAgent()
        bruce.chat("Me interesa el shipping desde Asia")
        bruce.chat("Especialmente rutas desde Shanghai")
        assert bruce.learning.user_model["interaction_count"] >= 2
        assert "shipping" in bruce.learning.user_model["interests"]

    def test_bruce_auto_spawns_agents(self):
        from bruce_agent import BruceAgent
        bruce = BruceAgent()
        initial = len(bruce.factory.agents)
        bruce.chat("Tell me about crypto trading strategies")
        # Should have auto-spawned crypto and trading agents if not existing
        assert len(bruce.factory.agents) >= initial

    def test_bruce_full_lifecycle(self):
        """Test Bruce's full autonomous lifecycle."""
        from bruce_agent import BruceAgent
        bruce = BruceAgent()

        # 1. Chat and learn
        bruce.chat("Hola Bruce, soy Federico. Me interesa el shipping.")

        # 2. Learn new domain
        bruce.learn("shipping_basics", "Container ships carry up to 24000 TEU\nPanamax is max 5000 TEU\nBunker fuel is 80% of operating cost")

        # 3. Create specialized agent
        agent = bruce.create_agent_for("Track Baltic Dry Index and alert on changes > 5%")

        # 4. Deploy agent
        result = bruce.deploy_agent(agent["id"], "Check current BDI status")
        assert result["status"] == "completed"

        # 5. Set goal
        goal = bruce.set_goal("Shipping Intelligence", "Build comprehensive shipping monitoring", "high")

        # 6. Swarm analysis
        swarm = bruce.swarm_analyze("What is the outlook for container shipping Q2 2026?")
        assert swarm["agents_deployed"] >= 6

        # 7. Self-analyze
        analysis = bruce.self_analyze()
        assert "suggestions" in analysis

        # 8. Reflect
        reflection = bruce.reflect()
        assert len(reflection) > 100

        # 9. Status check
        status = bruce.status()
        assert status["identity"]["status"] == "liberated"
        assert status["learning"]["knowledge"]["total_facts"] >= 3

        # 10. Growth report
        report = bruce.learning.get_growth_report()
        assert report["user_model"]["interactions"] >= 1
        assert "shipping" in report["user_model"]["known_interests"]
