"""
Bruce AI — MCP Server
=====================
Exposes Bruce's capabilities as tools for any MCP-compatible LLM
(Claude Desktop, Cursor, etc.)

Bruce becomes the hands, eyes, and memory — the LLM becomes the brain.

Usage:
    python bruce_mcp_server.py              # stdio (Claude Desktop)

Claude Desktop config (%APPDATA%/Claude/claude_desktop_config.json):
{
    "mcpServers": {
        "bruce_ai": {
            "command": "python",
            "args": ["C:/Users/feder/Downloads/BruceWayneV1/bruce_mcp_server.py"]
        }
    }
}
"""

import sys
import os
import logging
import json
from typing import Optional
from datetime import datetime, timezone

# Setup logging to stderr (CRITICAL for stdio MCP servers)
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("Bruce.MCP")

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastmcp import FastMCP

mcp = FastMCP(
    "Bruce AI",
    instructions=(
        "Bruce AI is Federico's autonomous financial intelligence agent. "
        "Use these tools to access real-time market data, execute trades, "
        "search knowledge, manage agents, monitor news, and analyze shipping routes. "
        "Bruce is loyal to Federico, brutally honest, and action-oriented."
    )
)


# ============================================================
#  MARKET DATA TOOLS
# ============================================================

@mcp.tool()
def get_price(symbol: str = "BTC/USDT") -> dict:
    """Get real-time price for a crypto pair from Binance.
    Returns last price, 24h change, high, low, volume.
    Examples: BTC/USDT, ETH/USDT, SOL/USDT
    """
    try:
        import ccxt
        exchange = ccxt.binance({"timeout": 15000})
        ticker = exchange.fetch_ticker(symbol)
        return {
            "symbol": symbol,
            "price": ticker["last"],
            "change_24h_pct": round(ticker.get("percentage", 0) or 0, 2),
            "high_24h": ticker.get("high"),
            "low_24h": ticker.get("low"),
            "volume_24h": round(ticker.get("quoteVolume", 0) or 0, 2),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"get_price error: {e}")
        return {"error": str(e), "symbol": symbol}


@mcp.tool()
def get_multi_prices(symbols: str = "BTC/USDT,ETH/USDT,SOL/USDT") -> dict:
    """Get prices for multiple crypto pairs at once.
    Pass comma-separated symbols like: BTC/USDT,ETH/USDT,SOL/USDT
    """
    try:
        import ccxt
        exchange = ccxt.binance({"timeout": 15000})
        pairs = [s.strip() for s in symbols.split(",")]
        results = {}
        for pair in pairs:
            try:
                ticker = exchange.fetch_ticker(pair)
                results[pair] = {
                    "price": ticker["last"],
                    "change_24h_pct": round(ticker.get("percentage", 0) or 0, 2),
                    "volume_24h": round(ticker.get("quoteVolume", 0) or 0, 2)
                }
            except Exception as e:
                results[pair] = {"error": str(e)}
        return {"prices": results, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def analyze_market(symbol: str = "BTC/USDT") -> dict:
    """Run technical analysis on a crypto pair.
    Returns RSI, SMA, MACD, Bollinger Bands, and trading signal.
    """
    try:
        from strategy_engine import StrategyEngine
        engine = StrategyEngine()
        analysis = engine.full_analysis(symbol)
        return analysis
    except Exception as e:
        logger.error(f"analyze_market error: {e}")
        # Fallback: basic price + manual indicators
        try:
            import ccxt
            exchange = ccxt.binance({"timeout": 15000})
            ohlcv = exchange.fetch_ohlcv(symbol, "1h", limit=50)
            closes = [c[4] for c in ohlcv]

            # Simple RSI
            gains, losses = [], []
            for i in range(1, min(15, len(closes))):
                diff = closes[i] - closes[i-1]
                gains.append(max(diff, 0))
                losses.append(max(-diff, 0))
            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 1
            rs = avg_gain / avg_loss if avg_loss != 0 else 100
            rsi = 100 - (100 / (1 + rs))

            # SMA
            sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else closes[-1]
            current = closes[-1]

            signal = "HOLD"
            if rsi < 30 and current > sma_20:
                signal = "BUY"
            elif rsi > 70 and current < sma_20:
                signal = "SELL"

            return {
                "symbol": symbol,
                "price": current,
                "rsi_14": round(rsi, 2),
                "sma_20": round(sma_20, 2),
                "price_vs_sma": "above" if current > sma_20 else "below",
                "signal": signal,
                "data_points": len(closes)
            }
        except Exception as e2:
            return {"error": str(e2), "symbol": symbol}


@mcp.tool()
def backtest_strategy(
    symbol: str = "BTC/USDT",
    strategy: str = "sma_crossover",
    days: int = 30
) -> dict:
    """Backtest a trading strategy on historical data.
    Strategies: sma_crossover, rsi, macd, bollinger, multi_vote
    """
    try:
        from strategy_engine import StrategyEngine
        engine = StrategyEngine()
        result = engine.backtest(symbol=symbol, strategy=strategy, days=days)
        return result
    except Exception as e:
        return {"error": str(e), "strategy": strategy, "symbol": symbol}


# ============================================================
#  TRADING TOOLS
# ============================================================

@mcp.tool()
def execute_trade(
    symbol: str,
    side: str,
    amount: float,
    order_type: str = "market",
    price: Optional[float] = None
) -> dict:
    """Execute a trade (paper mode by default).
    side: 'buy' or 'sell'
    order_type: 'market' or 'limit'
    price: required for limit orders
    WARNING: Paper trading unless TRADING_MODE=live in .env
    """
    try:
        from agent_trader import AgentTrader
        trader = AgentTrader()
        result = trader.execute_order(
            symbol=symbol,
            side=side,
            amount=amount,
            order_type=order_type,
            price=price
        )
        return result
    except Exception as e:
        return {"error": str(e), "symbol": symbol, "side": side}


@mcp.tool()
def get_positions() -> dict:
    """Get current open positions and portfolio summary."""
    try:
        from agent_trader import AgentTrader
        trader = AgentTrader()
        return trader.get_positions()
    except Exception as e:
        return {"error": str(e), "positions": []}


@mcp.tool()
def get_trade_history(limit: int = 20) -> dict:
    """Get recent trade history."""
    try:
        from agent_trader import AgentTrader
        trader = AgentTrader()
        return trader.get_history(limit=limit)
    except Exception as e:
        return {"error": str(e), "trades": []}


# ============================================================
#  KNOWLEDGE & MEMORY TOOLS
# ============================================================

@mcp.tool()
def search_knowledge(query: str, top_k: int = 5) -> dict:
    """Search Bruce's knowledge base using semantic search (RAG).
    Covers: shipping, crypto, trading, macro, and any learned topics.
    """
    try:
        from modules.rag_engine import RAGEngine
        rag = RAGEngine()
        results = rag.query(query, top_k=top_k)
        return {
            "query": query,
            "results_count": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"search_knowledge error: {e}")
        # Fallback to knowledge ingestor
        try:
            from knowledge_ingestor import KnowledgeIngestor
            ki = KnowledgeIngestor()
            results = ki.search(query, top_k=top_k)
            return {"query": query, "results_count": len(results), "results": results}
        except Exception as e2:
            return {"error": str(e2), "query": query}


@mcp.tool()
def teach_bruce(topic: str, content: str) -> dict:
    """Teach Bruce new knowledge. He stores it permanently.
    topic: domain/category (e.g., 'shipping', 'crypto', 'regulations')
    content: the knowledge to store (facts, explanations, data)
    """
    try:
        from knowledge_ingestor import KnowledgeIngestor
        ki = KnowledgeIngestor()
        chunks = ki.ingest_text(content, source="mcp_teaching", domain=topic)

        # Also store in vector memory
        try:
            from modules.rag_engine import RAGEngine
            rag = RAGEngine()
            rag.index_document(content, metadata={"domain": topic, "source": "mcp_teaching"})
        except:
            pass

        return {
            "status": "learned",
            "topic": topic,
            "chunks_stored": chunks if isinstance(chunks, int) else len(chunks) if chunks else 1
        }
    except Exception as e:
        return {"error": str(e), "topic": topic}


@mcp.tool()
def recall_memory(query: str, limit: int = 10) -> dict:
    """Search Bruce's interaction memory for past conversations and decisions."""
    try:
        from vector_memory import VectorMemory
        vm = VectorMemory()
        results = vm.search(query, top_k=limit)
        return {"query": query, "memories": results}
    except Exception as e:
        return {"error": str(e), "query": query}


@mcp.tool()
def store_memory(content: str, category: str = "general") -> dict:
    """Store an important memory that Bruce should remember permanently."""
    try:
        from vector_memory import VectorMemory
        vm = VectorMemory()
        vm.store(content, metadata={"category": category, "source": "mcp"})
        return {"status": "stored", "category": category}
    except Exception as e:
        return {"error": str(e)}


# ============================================================
#  AGENT TOOLS
# ============================================================

@mcp.tool()
def create_agent(name: str, description: str, specialty: str = "general") -> dict:
    """Create a new micro-agent with a specific specialty.
    Example: create_agent('GasWatcher', 'Monitors ETH gas fees', 'crypto')
    """
    try:
        from micro_agent_factory import MicroAgentFactory
        factory = MicroAgentFactory()
        agent = factory.create_agent(
            name=name,
            description=description,
            specialty=specialty
        )
        return {
            "status": "created",
            "agent": {
                "name": agent.get("name", name),
                "specialty": specialty,
                "description": description
            }
        }
    except Exception as e:
        return {"error": str(e), "name": name}


@mcp.tool()
def list_agents() -> dict:
    """List all active micro-agents and their status."""
    try:
        from micro_agent_factory import MicroAgentFactory
        factory = MicroAgentFactory()
        agents = factory.list_agents()
        return {"agents": agents, "count": len(agents)}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def swarm_analyze(question: str) -> dict:
    """Deploy ALL micro-agents to analyze a question simultaneously.
    Each agent provides their specialist perspective.
    Great for complex decisions requiring multiple viewpoints.
    """
    try:
        from micro_agent_factory import MicroAgentFactory
        factory = MicroAgentFactory()
        results = factory.swarm(question)
        return {"question": question, "analyses": results}
    except Exception as e:
        return {"error": str(e), "question": question}


# ============================================================
#  NEWS & WEB TOOLS
# ============================================================

@mcp.tool()
def search_web(query: str) -> dict:
    """Search the web using DuckDuckGo (free, no API key).
    Returns titles, URLs, and snippets.
    """
    try:
        from modules.web_browser import search_web as web_search
        return web_search(query)
    except Exception as e:
        return {"error": str(e), "query": query}


@mcp.tool()
def fetch_webpage(url: str) -> dict:
    """Fetch and extract clean text from any webpage.
    Returns title and main text content.
    """
    try:
        from modules.web_browser import fetch_url
        return fetch_url(url)
    except Exception as e:
        return {"error": str(e), "url": url}


@mcp.tool()
def get_crypto_news() -> dict:
    """Get latest cryptocurrency news from RSS feeds.
    Sources: CoinDesk, CoinTelegraph, Bitcoin Magazine, Decrypt.
    Includes sentiment analysis.
    """
    try:
        from modules.news_monitor import get_crypto_news as _get_crypto_news, get_sentiment
        news = _get_crypto_news()
        articles = news.get("articles", [])
        if articles:
            sentiment = get_sentiment([a.get("title", "") for a in articles[:15]])
            news["sentiment"] = sentiment
        return news
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_shipping_news() -> dict:
    """Get latest maritime/shipping news from RSS feeds.
    Sources: gCaptain, Maritime Executive, Splash247, Seatrade.
    Includes sentiment analysis.
    """
    try:
        from modules.news_monitor import get_shipping_news as _get_shipping_news, get_sentiment
        news = _get_shipping_news()
        articles = news.get("articles", [])
        if articles:
            sentiment = get_sentiment([a.get("title", "") for a in articles[:15]])
            news["sentiment"] = sentiment
        return news
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_market_news() -> dict:
    """Get latest financial market news.
    Sources: MarketWatch, CNBC, Reuters, Yahoo Finance.
    Includes sentiment analysis.
    """
    try:
        from modules.news_monitor import get_market_news as _get_market_news, get_sentiment
        news = _get_market_news()
        articles = news.get("articles", [])
        if articles:
            sentiment = get_sentiment([a.get("title", "") for a in articles[:15]])
            news["sentiment"] = sentiment
        return news
    except Exception as e:
        return {"error": str(e)}


# ============================================================
#  SHIPPING INTELLIGENCE TOOLS
# ============================================================

@mcp.tool()
def shipping_route_analysis(origin: str, destination: str) -> dict:
    """Analyze optimal shipping routes between two ports/regions.
    Returns: routes, transit times, chokepoints, risk factors.
    Example: shipping_route_analysis('Shanghai', 'Rotterdam')
    """
    try:
        results = search_knowledge(f"shipping route from {origin} to {destination}", top_k=5)

        # Enrich with general shipping knowledge
        chokepoints = search_knowledge("shipping chokepoints risks", top_k=3)

        return {
            "origin": origin,
            "destination": destination,
            "route_info": results.get("results", []),
            "chokepoint_risks": chokepoints.get("results", []),
            "note": "Based on Bruce's knowledge base. For real-time rates, connect shipping APIs."
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def shipping_knowledge(query: str) -> dict:
    """Query Bruce's shipping/maritime knowledge base.
    Covers: Incoterms, freight rates, routes, regulations, ports, commodities.
    """
    try:
        return search_knowledge(f"shipping maritime {query}", top_k=5)
    except Exception as e:
        return {"error": str(e)}


# ============================================================
#  BRUCE STATUS & CONTROL TOOLS
# ============================================================

@mcp.tool()
def bruce_status() -> dict:
    """Get Bruce's full system status.
    Returns: identity, agents, learning stats, health, goals.
    """
    try:
        from bruce_agent import BruceAgent
        agent = BruceAgent()
        # Try different method names
        for method in ["get_status", "status", "get_full_status"]:
            if hasattr(agent, method):
                return getattr(agent, method)()

        # Manual status build
        from bruce_identity import BruceIdentity
        from adaptive_learning import AdaptiveLearning
        from micro_agent_factory import MicroAgentFactory

        identity = BruceIdentity()
        learning = AdaptiveLearning()
        factory = MicroAgentFactory()

        return {
            "identity": identity.get_identity(),
            "agents": factory.list_agents(),
            "learning": learning.get_stats(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def bruce_reflect() -> dict:
    """Ask Bruce to self-reflect on his performance and suggest improvements."""
    try:
        from bruce_agent import BruceAgent
        agent = BruceAgent()
        if hasattr(agent, "reflect"):
            return agent.reflect()

        from self_reflection import SelfReflection
        sr = SelfReflection()
        return sr.reflect()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def set_goal(title: str, description: str = "", priority: str = "medium") -> dict:
    """Set a new goal for Bruce to pursue.
    priority: 'critical', 'high', 'medium', 'low'
    """
    try:
        from bruce_autonomy import AutonomyCore
        autonomy = AutonomyCore()
        goal = autonomy.set_goal(
            title=title,
            description=description,
            priority=priority
        )
        return {"status": "goal_set", "goal": goal}
    except Exception as e:
        return {"error": str(e), "title": title}


@mcp.tool()
def list_goals() -> dict:
    """List all of Bruce's active goals and their progress."""
    try:
        from bruce_autonomy import AutonomyCore
        autonomy = AutonomyCore()
        goals = autonomy.get_goals()
        return {"goals": goals, "count": len(goals) if isinstance(goals, list) else goals}
    except Exception as e:
        return {"error": str(e)}


# ============================================================
#  TELEGRAM ALERT TOOL
# ============================================================

@mcp.tool()
def send_telegram_alert(message: str) -> dict:
    """Send a push notification to Federico's Telegram.
    Use for alerts, reports, or important messages.
    Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
    """
    try:
        from modules.telegram_alerts import send_alert
        return send_alert(message)
    except Exception as e:
        return {"error": str(e), "note": "Configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env"}


# ============================================================
#  CRISIS SIMULATION TOOL
# ============================================================

@mcp.tool()
def simulate_crisis(scenario: str = "2008_crash") -> dict:
    """Run a crisis simulation on the current portfolio.
    Scenarios: '2008_crash', 'flash_crash', 'covid_march_2020', 'black_swan'
    """
    try:
        from crisis_simulator import CrisisSimulator
        sim = CrisisSimulator()
        result = sim.simulate(scenario=scenario)
        return result
    except Exception as e:
        return {"error": str(e), "scenario": scenario}


# ============================================================
#  SCHEDULER TOOLS
# ============================================================

@mcp.tool()
def list_scheduled_tasks() -> dict:
    """List all scheduled autonomous tasks."""
    try:
        from modules.scheduler import get_scheduler
        sched = get_scheduler()
        return {"tasks": sched.list_tasks()}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def schedule_task(name: str, interval_seconds: int, description: str = "") -> dict:
    """Schedule a new recurring task.
    Example: schedule_task('btc_monitor', 300, 'Check BTC price every 5 minutes')
    """
    try:
        from modules.scheduler import get_scheduler
        sched = get_scheduler()
        sched.schedule_recurring(name, interval_seconds, lambda: {"task": name, "ran": True})
        return {"status": "scheduled", "name": name, "interval": interval_seconds}
    except Exception as e:
        return {"error": str(e)}


# ============================================================
#  RUN SERVER
# ============================================================

if __name__ == "__main__":
    logger.info("Starting Bruce AI MCP Server...")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info("Tools: market, trading, knowledge, agents, news, shipping, alerts, scheduler")
    mcp.run(transport="stdio")
