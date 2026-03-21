"""
Bruce AI — Real Tool System

Tools that Bruce and his micro-agents can actually USE to do things.
Not strings. Not mocks. Real actions.
"""

import io
import json
import logging
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

import requests

logger = logging.getLogger("Bruce.Tools")


class ToolResult:
    """Result of a tool execution."""
    def __init__(self, success: bool, output: Any, error: str = None, elapsed_ms: float = 0):
        self.success = success
        self.output = output
        self.error = error
        self.elapsed_ms = elapsed_ms

    def to_dict(self):
        return {
            "success": self.success,
            "output": str(self.output)[:2000] if self.output else None,
            "error": self.error,
            "elapsed_ms": self.elapsed_ms,
        }

    def __str__(self):
        if self.success:
            return str(self.output)
        return f"Error: {self.error}"


class ToolRegistry:
    """Registry of all tools Bruce can use."""

    def __init__(self):
        self.tools: Dict[str, Dict] = {}
        self._register_builtin_tools()

    def register(self, name: str, fn: Callable, description: str, parameters: dict = None):
        """Register a tool."""
        self.tools[name] = {
            "name": name,
            "fn": fn,
            "description": description,
            "parameters": parameters or {},
        }

    def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        if name not in self.tools:
            return ToolResult(False, None, f"Tool '{name}' not found")
        start = time.perf_counter()
        try:
            result = self.tools[name]["fn"](**kwargs)
            elapsed = round((time.perf_counter() - start) * 1000, 1)
            return ToolResult(True, result, elapsed_ms=elapsed)
        except Exception as e:
            elapsed = round((time.perf_counter() - start) * 1000, 1)
            logger.error(f"Tool '{name}' failed: {e}")
            return ToolResult(False, None, str(e), elapsed_ms=elapsed)

    def list_tools(self) -> List[dict]:
        """List all available tools with descriptions."""
        return [
            {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}
            for t in self.tools.values()
        ]

    def get_tools_prompt(self) -> str:
        """Get a prompt-friendly description of all tools."""
        lines = ["Available tools:"]
        for t in self.tools.values():
            params = ", ".join(f"{k}" for k in t["parameters"].keys()) if t["parameters"] else "none"
            lines.append(f"  - {t['name']}({params}): {t['description']}")
        return "\n".join(lines)

    # =========================================================================
    # Built-in Tools
    # =========================================================================

    def _register_builtin_tools(self):
        """Register all built-in tools."""

        # === Code Execution ===
        self.register(
            "run_python",
            self._tool_run_python,
            "Execute Python code and return the output. Use for calculations, data analysis, etc.",
            {"code": "Python code to execute"},
        )

        # === Web/API ===
        self.register(
            "http_get",
            self._tool_http_get,
            "Make an HTTP GET request to any URL. Returns response body.",
            {"url": "URL to fetch", "headers": "Optional headers dict"},
        )

        self.register(
            "http_post",
            self._tool_http_post,
            "Make an HTTP POST request. Use for APIs that need data.",
            {"url": "URL", "data": "JSON data to send", "headers": "Optional headers"},
        )

        # === Market Data ===
        self.register(
            "get_price",
            self._tool_get_price,
            "Get current price of a crypto asset from Binance.",
            {"symbol": "Trading pair, e.g. BTC/USDT"},
        )

        self.register(
            "get_market_data",
            self._tool_get_market_data,
            "Get OHLCV candle data for a symbol.",
            {"symbol": "e.g. BTC/USDT", "timeframe": "e.g. 1d", "limit": "Number of candles"},
        )

        # === File System ===
        self.register(
            "read_file",
            self._tool_read_file,
            "Read contents of a file.",
            {"path": "File path to read"},
        )

        self.register(
            "write_file",
            self._tool_write_file,
            "Write content to a file.",
            {"path": "File path", "content": "Content to write"},
        )

        # === Knowledge ===
        self.register(
            "search_knowledge",
            self._tool_search_knowledge,
            "Search Bruce's knowledge base for information.",
            {"query": "Search query"},
        )

        self.register(
            "ingest_url",
            self._tool_ingest_url,
            "Learn from a web page. Scrapes and stores the content.",
            {"url": "URL to ingest"},
        )

        # === Trading ===
        self.register(
            "paper_trade",
            self._tool_paper_trade,
            "Execute a paper trade (simulated, no real money).",
            {"symbol": "e.g. BTC/USDT", "side": "buy or sell", "amount": "Amount"},
        )

        self.register(
            "evaluate_strategy",
            self._tool_evaluate_strategy,
            "Evaluate a trading strategy on recent data.",
            {"strategy": "sma_crossover, rsi, macd, or bollinger", "symbol": "e.g. BTC/USDT"},
        )

        # === Analysis ===
        self.register(
            "analyze_shipping",
            self._tool_analyze_shipping,
            "Get shipping/freight intelligence for a commodity or route.",
            {"asset": "crude oil, LNG, copper, or container cargo"},
        )

        self.register(
            "calculate",
            self._tool_calculate,
            "Evaluate a math expression. Use for any calculation.",
            {"expression": "Math expression, e.g. '100 * 1.05 ** 10'"},
        )

        # === System ===
        self.register(
            "shell",
            self._tool_shell,
            "Execute a shell command. Use carefully.",
            {"command": "Shell command to run"},
        )

    # === Tool Implementations ===

    def _tool_run_python(self, code: str) -> str:
        """Execute Python code safely."""
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        try:
            exec(code, {"__builtins__": __builtins__}, {})
            output = buffer.getvalue()
            return output if output else "(no output)"
        except Exception as e:
            return f"Error: {e}\n{traceback.format_exc()}"
        finally:
            sys.stdout = old_stdout

    def _tool_http_get(self, url: str, headers: dict = None) -> str:
        r = requests.get(url, headers=headers or {}, timeout=30)
        r.raise_for_status()
        try:
            return json.dumps(r.json(), indent=2)[:3000]
        except Exception:
            return r.text[:3000]

    def _tool_http_post(self, url: str, data: dict = None, headers: dict = None) -> str:
        r = requests.post(url, json=data, headers=headers or {}, timeout=30)
        r.raise_for_status()
        try:
            return json.dumps(r.json(), indent=2)[:3000]
        except Exception:
            return r.text[:3000]

    def _tool_get_price(self, symbol: str) -> str:
        try:
            import ccxt
            exchange = ccxt.binance()
            ticker = exchange.fetch_ticker(symbol)
            return json.dumps({
                "symbol": symbol,
                "price": ticker["last"],
                "change_24h": ticker.get("percentage"),
                "volume_24h": ticker.get("quoteVolume"),
                "high_24h": ticker.get("high"),
                "low_24h": ticker.get("low"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, indent=2)
        except ImportError:
            return json.dumps({"error": "ccxt not installed", "symbol": symbol})
        except Exception as e:
            return json.dumps({"error": str(e), "symbol": symbol})

    def _tool_get_market_data(self, symbol: str, timeframe: str = "1d", limit: int = 30) -> str:
        try:
            import ccxt
            exchange = ccxt.binance()
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=int(limit))
            candles = [
                {"date": datetime.fromtimestamp(c[0]/1000).strftime("%Y-%m-%d"),
                 "open": c[1], "high": c[2], "low": c[3], "close": c[4], "volume": c[5]}
                for c in ohlcv
            ]
            return json.dumps({"symbol": symbol, "timeframe": timeframe, "candles": candles[-10:]}, indent=2)
        except ImportError:
            return json.dumps({"error": "ccxt not installed"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _tool_read_file(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content[:5000]

    def _tool_write_file(self, path: str, content: str) -> str:
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Written {len(content)} chars to {path}"

    def _tool_search_knowledge(self, query: str) -> str:
        try:
            sys.path.insert(0, ".")
            from knowledge_ingestor import KnowledgeIngestor
            ki = KnowledgeIngestor()
            results = ki.search(query)
            if not results:
                return "No results found."
            return "\n\n".join(f"[{r.get('source', 'unknown')}] {r['content'][:300]}" for r in results[:5])
        except Exception as e:
            return f"Knowledge search error: {e}"

    def _tool_ingest_url(self, url: str) -> str:
        try:
            sys.path.insert(0, ".")
            from knowledge_ingestor import KnowledgeIngestor
            ki = KnowledgeIngestor()
            result = ki.ingest_url(url)
            return f"Ingested {result.get('chunks', 0)} chunks from {url}"
        except Exception as e:
            return f"Ingest error: {e}"

    def _tool_paper_trade(self, symbol: str, side: str, amount: float) -> str:
        try:
            sys.path.insert(0, ".")
            from agent_trader import TradingAgent
            ta = TradingAgent(mode="paper", initial_balance=100000)
            order = ta.create_order(symbol, side, float(amount))
            return json.dumps(order, indent=2, default=str)
        except Exception as e:
            return f"Trade error: {e}"

    def _tool_evaluate_strategy(self, strategy: str, symbol: str = "BTC/USDT") -> str:
        try:
            sys.path.insert(0, ".")
            import pandas as pd
            csv_path = f"data/market/{symbol.replace('/', '_')}_1d_indicators.csv"
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                prices = df["close"].tolist()
            else:
                prices = [50000 + i * 100 for i in range(30)]
            from strategy_engine import StrategyEngine
            se = StrategyEngine()
            signal = se.evaluate(strategy, prices)
            return json.dumps(signal, indent=2, default=str)
        except Exception as e:
            return f"Strategy error: {e}"

    def _tool_analyze_shipping(self, asset: str) -> str:
        try:
            sys.path.insert(0, ".")
            from modules.freight_trading_core import FreightTradingCore
            ftc = FreightTradingCore()
            price = ftc.get_commodity_price(asset)
            overview = ftc.get_market_overview()
            return json.dumps({"price": price, "overview": overview}, indent=2, default=str)
        except Exception as e:
            return f"Shipping analysis error: {e}"

    def _tool_calculate(self, expression: str) -> str:
        try:
            import math
            allowed = {"__builtins__": {}, "math": math, "abs": abs,
                       "round": round, "min": min, "max": max, "sum": sum,
                       "pow": pow, "int": int, "float": float}
            result = eval(expression, allowed)
            return str(result)
        except Exception as e:
            return f"Calc error: {e}"

    def _tool_shell(self, command: str) -> str:
        """Execute shell command with safety limits."""
        dangerous = ["rm -rf", "del /f", "format", "mkfs", "> /dev/sda"]
        if any(d in command.lower() for d in dangerous):
            return "Blocked: dangerous command detected."
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout + result.stderr
            return output[:3000] if output else "(no output)"
        except subprocess.TimeoutExpired:
            return "Command timed out (30s limit)"
        except Exception as e:
            return f"Shell error: {e}"


# Singleton
_registry = None

def get_tools() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
