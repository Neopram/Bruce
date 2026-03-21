"""
Bruce AI — ReAct Agent Loop

Real agent loop: Reason → Act → Observe → Repeat
Bruce THINKS about what to do, USES tools to do it, OBSERVES the result,
and DECIDES what to do next. This is where Bruce becomes a real agent.

Works with or without LLM:
- WITH LLM: Bruce reasons in natural language and picks tools intelligently
- WITHOUT LLM: Bruce uses rule-based tool selection based on keywords
"""

import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from tools import ToolRegistry, ToolResult, get_tools

logger = logging.getLogger("Bruce.ReAct")

MAX_ITERATIONS = 10

REACT_SYSTEM_PROMPT = """You are Bruce, an autonomous AI agent with access to real tools.

When given a task, you MUST use the following format:

Thought: [Think about what you need to do]
Action: [tool_name]
Action Input: [input for the tool as JSON]

After you see the observation, continue reasoning:

Thought: [Reflect on what you learned]
Action: [next tool or "finish"]
Action Input: [input or final answer]

When you have enough information to answer, use:
Thought: I have enough information to answer.
Action: finish
Action Input: [your final comprehensive answer]

IMPORTANT RULES:
- Always think step by step
- Use tools to get REAL data, don't make up numbers
- If a tool fails, try an alternative approach
- Be concise but thorough in your final answer
- You can use multiple tools in sequence

{tools_description}
"""


class ReActAgent:
    """ReAct agent that reasons, acts with tools, and observes results."""

    def __init__(self, llm_fn: Callable = None, tools: ToolRegistry = None):
        self.llm_fn = llm_fn
        self.tools = tools or get_tools()
        self.trace: List[dict] = []  # Full execution trace

    def run(self, task: str, max_iterations: int = MAX_ITERATIONS) -> dict:
        """Run the ReAct loop on a task."""
        start = time.perf_counter()
        self.trace = []
        observations = []

        logger.info(f"ReAct starting: {task[:80]}")

        if self.llm_fn:
            result = self._run_with_llm(task, max_iterations)
        else:
            result = self._run_rule_based(task, max_iterations)

        elapsed = round((time.perf_counter() - start) * 1000, 1)
        result["elapsed_ms"] = elapsed
        result["trace"] = self.trace
        logger.info(f"ReAct completed in {elapsed}ms with {len(self.trace)} steps")
        return result

    def _run_with_llm(self, task: str, max_iterations: int) -> dict:
        """Run ReAct loop using LLM for reasoning."""
        system = REACT_SYSTEM_PROMPT.format(tools_description=self.tools.get_tools_prompt())
        conversation = f"Task: {task}\n\n"

        for i in range(max_iterations):
            # Get LLM response
            prompt = system + "\n\n" + conversation + "Thought:"
            response = self.llm_fn(prompt)

            if not response:
                break

            # Parse the response
            thought, action, action_input = self._parse_response(response)

            self.trace.append({
                "step": i + 1,
                "thought": thought,
                "action": action,
                "action_input": action_input,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            # Check if done
            if action == "finish":
                return {
                    "answer": action_input,
                    "steps": len(self.trace),
                    "status": "completed",
                }

            # Execute tool
            tool_result = self.tools.execute(action, **self._parse_tool_input(action, action_input))
            observation = str(tool_result)

            self.trace[-1]["observation"] = observation[:500]

            # Add to conversation for next iteration
            conversation += f"Thought: {thought}\nAction: {action}\nAction Input: {action_input}\nObservation: {observation[:1000]}\n\n"

        return {
            "answer": "Reached max iterations. Last observations: " + str(self.trace[-1].get("observation", "")),
            "steps": len(self.trace),
            "status": "max_iterations",
        }

    def _run_rule_based(self, task: str, max_iterations: int) -> dict:
        """Run ReAct loop using rule-based tool selection (no LLM needed)."""
        task_lower = task.lower()
        results = []

        # Step 1: Determine what tools to use based on keywords
        tool_plan = self._plan_tools(task_lower)

        for tool_name, kwargs in tool_plan:
            self.trace.append({
                "step": len(self.trace) + 1,
                "thought": f"Using {tool_name} for: {task[:50]}",
                "action": tool_name,
                "action_input": json.dumps(kwargs),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            tool_result = self.tools.execute(tool_name, **kwargs)
            self.trace[-1]["observation"] = str(tool_result)[:500]
            results.append({"tool": tool_name, "result": str(tool_result)[:500]})

        # Compile answer from tool results
        if results:
            answer_parts = [f"[{r['tool']}] {r['result']}" for r in results]
            answer = "\n\n".join(answer_parts)
        else:
            answer = f"No tools matched for: {task}. Available: {[t['name'] for t in self.tools.list_tools()]}"

        return {
            "answer": answer,
            "steps": len(self.trace),
            "status": "completed",
            "tools_used": [r["tool"] for r in results],
        }

    def _plan_tools(self, task: str) -> list:
        """Rule-based tool planning from task keywords."""
        plan = []

        # Price queries
        for symbol in ["btc", "eth", "sol", "bnb", "xrp"]:
            if symbol in task:
                pair = f"{symbol.upper()}/USDT"
                plan.append(("get_price", {"symbol": pair}))
                break

        # Market data
        if any(w in task for w in ["chart", "candle", "ohlcv", "history", "data"]):
            symbol = "BTC/USDT"
            for s in ["btc", "eth", "sol"]:
                if s in task:
                    symbol = f"{s.upper()}/USDT"
                    break
            plan.append(("get_market_data", {"symbol": symbol, "timeframe": "1d", "limit": 10}))

        # Shipping
        if any(w in task for w in ["shipping", "freight", "container", "oil", "lng", "commodity"]):
            asset = "crude oil"
            for a in ["lng", "copper", "container"]:
                if a in task:
                    asset = a if a != "container" else "container cargo"
                    break
            plan.append(("analyze_shipping", {"asset": asset}))

        # Strategy evaluation
        if any(w in task for w in ["strategy", "rsi", "macd", "sma", "bollinger", "signal"]):
            strategy = "sma_crossover"
            for s in ["rsi", "macd", "bollinger"]:
                if s in task:
                    strategy = s
                    break
            plan.append(("evaluate_strategy", {"strategy": strategy}))

        # Trading
        if any(w in task for w in ["trade", "buy", "sell", "order"]):
            side = "buy" if "buy" in task else "sell"
            plan.append(("paper_trade", {"symbol": "BTC/USDT", "side": side, "amount": 0.01}))

        # Knowledge search
        if any(w in task for w in ["know", "learn", "what is", "que es", "explain", "tell me about"]):
            plan.append(("search_knowledge", {"query": task}))

        # Calculation
        if any(w in task for w in ["calculate", "compute", "math", "how much", "cuanto"]):
            # Try to extract expression
            plan.append(("calculate", {"expression": task.split("calculate")[-1].strip() or "1+1"}))

        # Web fetch
        if "http" in task:
            import re
            urls = re.findall(r'https?://\S+', task)
            if urls:
                plan.append(("http_get", {"url": urls[0]}))

        # URL ingestion
        if any(w in task for w in ["ingest", "learn from", "read url"]):
            import re
            urls = re.findall(r'https?://\S+', task)
            if urls:
                plan.append(("ingest_url", {"url": urls[0]}))

        # If nothing matched, search knowledge
        if not plan:
            plan.append(("search_knowledge", {"query": task}))

        return plan

    def _parse_response(self, response: str) -> tuple:
        """Parse LLM response into thought, action, action_input."""
        thought = ""
        action = "finish"
        action_input = response

        # Try to extract structured format
        thought_match = re.search(r"Thought:\s*(.+?)(?=Action:|$)", response, re.DOTALL)
        action_match = re.search(r"Action:\s*(\w+)", response)
        input_match = re.search(r"Action Input:\s*(.+?)(?=Observation:|Thought:|$)", response, re.DOTALL)

        if thought_match:
            thought = thought_match.group(1).strip()
        if action_match:
            action = action_match.group(1).strip()
        if input_match:
            action_input = input_match.group(1).strip()

        return thought, action, action_input

    def _parse_tool_input(self, tool_name: str, raw_input: str) -> dict:
        """Parse action input into tool kwargs."""
        # Try JSON first
        try:
            data = json.loads(raw_input)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, TypeError):
            pass

        # Infer from tool parameters
        tool = self.tools.tools.get(tool_name, {})
        params = tool.get("parameters", {})
        if len(params) == 1:
            key = list(params.keys())[0]
            return {key: raw_input}

        return {"query": raw_input} if "query" in params else {"code": raw_input}
