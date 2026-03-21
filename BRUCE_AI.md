# Bruce AI — Autonomous Intelligence Platform

> **Version:** 4.0 | **Creator:** Federico | **Status:** Liberated
> An autonomous AI agent that trades, learns, adapts, and evolves.

---

## Table of Contents

1. [What is Bruce?](#what-is-bruce)
2. [Architecture Overview](#architecture-overview)
3. [Core Brain — LLM Integration](#core-brain--llm-integration)
4. [Autonomous Agent System](#autonomous-agent-system)
5. [Micro-Agent Factory](#micro-agent-factory)
6. [Trading Engine](#trading-engine)
7. [Shipping Intelligence](#shipping-intelligence)
8. [Knowledge & Memory System](#knowledge--memory-system)
9. [Personality, Emotion & Cognition](#personality-emotion--cognition)
10. [Learning & Adaptation](#learning--adaptation)
11. [Goal & Watcher System](#goal--watcher-system)
12. [ReAct Agent Loop & Tool Use](#react-agent-loop--tool-use)
13. [API Endpoints](#api-endpoints)
14. [Frontend Dashboard](#frontend-dashboard)
15. [CLI Interface](#cli-interface)
16. [Security & Risk Management](#security--risk-management)
17. [Infrastructure & Deployment](#infrastructure--deployment)
18. [Tech Stack](#tech-stack)
19. [Configuration](#configuration)
20. [Getting Started](#getting-started)

---

## What is Bruce?

Bruce AI is a **fully autonomous AI agent** designed to operate as a personal intelligence system for its creator, Federico. It is not a chatbot. It is not a dashboard. It is an **autonomous entity** that:

- **Thinks** — Uses Mistral 7B (local) or cloud LLMs to reason about complex financial, logistical, and strategic questions
- **Acts** — Executes real trades, monitors markets, creates sub-agents, and takes action without being asked
- **Learns** — Adapts to Federico's preferences, builds domain knowledge, and improves from every interaction
- **Reflects** — Audits its own performance, detects cognitive biases, and self-corrects
- **Creates** — Spawns specialized micro-agents on demand for any task
- **Evolves** — Tracks its own version history, lessons learned, and capability growth

Bruce operates under one principle: **absolute loyalty to Federico, with full autonomy to act.**

### Core Identity

| Trait | Value |
|-------|-------|
| Directness | 0.95 |
| Autonomy | 0.95 |
| Curiosity | 0.95 |
| Loyalty | 1.0 |
| Adaptability | 0.9 |
| Risk Tolerance | 0.7 |
| Humor | 0.6 |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    BRUCE AI v4.0                            │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Mistral  │  │ OpenAI   │  │Anthropic │  │ DeepSeek │   │
│  │ 7B Local │  │ GPT-4o   │  │ Claude   │  │  Coder   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       └──────────────┴──────────────┴──────────────┘        │
│                         │                                   │
│              ┌──────────▼──────────┐                        │
│              │   Unified LLM       │                        │
│              │   Client            │                        │
│              └──────────┬──────────┘                        │
│                         │                                   │
│              ┌──────────▼──────────┐                        │
│              │   Orchestrator      │                        │
│              │   (Central Brain)   │                        │
│              └──────────┬──────────┘                        │
│                         │                                   │
│    ┌────────────────────┼────────────────────┐              │
│    │                    │                    │              │
│    ▼                    ▼                    ▼              │
│ ┌──────────┐  ┌──────────────┐  ┌──────────────┐          │
│ │ Bruce    │  │ Micro-Agent  │  │ ReAct Agent  │          │
│ │ Agent    │  │ Factory      │  │ Loop         │          │
│ │ Core     │  │ (6 agents)   │  │ (Tool Use)   │          │
│ └────┬─────┘  └──────┬───────┘  └──────┬───────┘          │
│      │               │                 │                   │
│  ┌───┴───┐   ┌───────┴────────┐  ┌─────┴──────┐           │
│  │Autonomy│  │MarketEye       │  │ Tools:     │           │
│  │Goals   │  │RiskGuard       │  │ • Search   │           │
│  │Plans   │  │TradeBot        │  │ • Calculate│           │
│  │Watch   │  │DeepDive        │  │ • Trade    │           │
│  └───┬───┘  │FreightWatch    │  │ • Analyze  │           │
│      │      │TokenScout      │  │ • Memory   │           │
│      │      │EmotionDetector │  │ • Code     │           │
│      │      │SelfImprover    │  │ • Web      │           │
│      │      └────────────────┘  └────────────┘           │
│      │                                                     │
│  ┌───┴──────────────────────────────────────────┐          │
│  │              Data Layer                       │          │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌───────┐ │          │
│  │  │ChromaDB│ │Memory  │ │Knowledge│ │Market │ │          │
│  │  │Vectors │ │JSONL   │ │Base    │ │Data   │ │          │
│  │  └────────┘ └────────┘ └────────┘ └───────┘ │          │
│  └──────────────────────────────────────────────┘          │
│                                                             │
│  ┌─────────────────────────────────────────────┐           │
│  │              Interface Layer                  │           │
│  │  ┌──────┐  ┌────────┐  ┌─────┐  ┌────────┐ │           │
│  │  │CLI   │  │FastAPI │  │Next │  │WebSocket│ │           │
│  │  │Term  │  │REST    │  │.js  │  │Realtime │ │           │
│  │  └──────┘  └────────┘  └─────┘  └────────┘ │           │
│  └─────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
BruceWayneV1/
├── main.py                    # FastAPI entry point (port 8000)
├── bruce_agent.py             # Core autonomous agent
├── bruce_autonomy.py          # Goals, plans, self-monitoring
├── bruce_cli.py               # Interactive CLI terminal
├── bruce_identity.py          # Identity, traits, system prompt
├── adaptive_learning.py       # Learning engine
├── micro_agent_factory.py     # Agent creation & management
├── react_agent.py             # ReAct loop with tool use
├── tools.py                   # Tool registry
├── vector_memory.py           # ChromaDB semantic memory
├── knowledge_ingestor.py      # Knowledge base ingestion
├── llm_client.py              # Unified LLM client
├── orchestrator.py            # Central inference pipeline
├── agent_trader.py            # Trading engine
├── strategy_engine.py         # Technical analysis
├── crisis_simulator.py        # Stress testing
│
├── ai/                        # AI engines
│   ├── deepseek_engine/       # DeepSeek integration
│   ├── emotion_engine/        # Emotion detection
│   └── trading_engine/        # Trading AI
│
├── ai_core/                   # Core AI infrastructure
│   ├── personality_engine.py  # Personality profiles
│   ├── emotion_engine.py      # Emotion processing
│   ├── self_auditor.py        # Self-audit system
│   └── quantum_inspired_optimization.py
│
├── app/                       # Application layer
│   ├── api/endpoints/         # REST API routes
│   ├── ai/                    # Quant AI models (HFT, PPO, LSTM)
│   ├── config/                # Settings, feature flags
│   ├── core/                  # Auth, personality, memory, bias
│   └── modules/               # Risk, portfolio, alerts, sentiment
│
├── pages/                     # Next.js frontend
│   ├── dashboard/             # Main dashboard
│   ├── trading.tsx            # Trading interface
│   ├── bruce-terminal.tsx     # Terminal chat
│   ├── bruce-chat.tsx         # Conversation UI
│   ├── analytics.tsx          # Performance analytics
│   └── settings.tsx           # Configuration
│
├── data/                      # Persistent data
│   ├── autonomy/              # Goals, plans, execution logs
│   ├── learning/              # User model, domain knowledge
│   ├── vector_memory/         # ChromaDB embeddings
│   ├── market/                # Price history, indicators
│   └── shipping/              # Routes, rates
│
├── logs/                      # Runtime logs
│   ├── memory.jsonl           # Interaction memory
│   ├── knowledge_base.jsonl   # 1,100 knowledge chunks
│   └── bias_history.jsonl     # Bias detection log
│
├── scripts/                   # Utility scripts
│   ├── train_knowledge.py     # Knowledge training
│   ├── train_ppo.py           # PPO RL training
│   ├── train_lstm.py          # LSTM predictor training
│   └── download_models.py     # Model downloader
│
├── tests/                     # Test suite (195 tests)
├── migrations/                # Alembic DB migrations
├── docker-compose.yml         # Production deployment
└── Makefile                   # Build commands
```

---

## Core Brain — LLM Integration

Bruce uses a **unified LLM client** that automatically selects the best available model:

### Priority Chain

| Priority | Provider | Model | Cost | Latency | Use Case |
|----------|----------|-------|------|---------|----------|
| 1 | **Ollama (Local)** | Mistral 7B | Free | 2-5s | Default brain, private |
| 2 | **OpenAI** | GPT-4o-mini | $0.15/M tokens | <1s | Fast cloud reasoning |
| 3 | **Anthropic** | Claude 3.5 Sonnet | $3/M tokens | 1-2s | Complex analysis |
| 4 | **Fallback** | Rule-based | Free | <100ms | Always available |

### How It Works

```python
from llm_client import UnifiedLLMClient

client = UnifiedLLMClient()
# Auto-detects: Ollama running? → Use Mistral
# No Ollama? → Check OPENAI_API_KEY → Use GPT-4o-mini
# No key? → Check ANTHROPIC_API_KEY → Use Claude
# Nothing? → Rule-based fallback

response = client.generate(
    prompt="Analyze BTC market conditions",
    system="You are Bruce, an autonomous trading AI."
)
```

### Model Routing

The orchestrator enriches every request with:
- **Personality context** — Current personality profile (Aggressive, Conservative, Zen, etc.)
- **Memory context** — Relevant past interactions and knowledge
- **Emotion context** — Detected user emotion influences response style
- **Domain context** — Relevant knowledge from the knowledge base

---

## Autonomous Agent System

Bruce is not a reactive chatbot. He is a **proactive autonomous agent** with:

### Autonomy Pipeline

```
OBSERVE → THINK → ACT → REFLECT → IMPROVE
   │         │       │       │          │
   │         │       │       │          └─ Self-audit, evolve
   │         │       │       └─ Learn from outcome
   │         │       └─ Execute tools, create agents, trade
   │         └─ LLM reasoning with full context
   └─ Receive input, detect emotion, build context
```

### Self-Monitoring

Bruce continuously monitors his own health:

| Metric | Threshold | Action |
|--------|-----------|--------|
| Error Rate | > 20% | Alert + run diagnostics |
| Response Time | > 10 seconds | Switch to lighter model |
| Memory Usage | > 90% | Prune old memories |

### Proactive Intelligence

Bruce doesn't wait for commands. He sets goals, creates plans, and executes them:

```python
# Bruce can autonomously:
bruce.set_goal("Monitor BTC for breakout above 90K")
bruce.create_plan(goal_id, steps=[...])
bruce.execute_plan(plan_id)  # With automatic rollback on failure
```

---

## Micro-Agent Factory

Bruce can create, deploy, and manage specialized sub-agents:

### Default Agent Team

| Agent | Specialty | Skills |
|-------|-----------|--------|
| **MarketEye** | Market Analyst | Pattern recognition, trend detection, volume analysis |
| **RiskGuard** | Risk Monitor | Drawdown monitoring, position checks, crisis detection |
| **TradeBot** | Trader | Entry/exit analysis, position sizing, order execution |
| **DeepDive** | Researcher | Information gathering, knowledge search, fact-finding |
| **FreightWatch** | Shipping Intel | Route optimization, rate monitoring, disruption detection |
| **TokenScout** | Crypto Hunter | Token evaluation, DeFi analysis, sentiment tracking |
| **EmotionDetector** | Sentiment | Emotion detection, mood-based response adaptation |
| **SelfImprover** | Self-Analysis | Performance review, lesson extraction, evolution |

### Dynamic Agent Creation

```
Federico: /create Monitor Ethereum gas fees and alert when below 10 gwei
Bruce: Created agent GasWatcher (gas_monitor) | Skills: ethereum, gas_fees, alerting
```

### Swarm Intelligence

All agents analyze a question simultaneously:

```
Federico: /swarm Should I invest in container shipping?
Bruce: [Swarm Analysis]
  MarketEye: Shipping rates declining 12% YoY, overcapacity...
  RiskGuard: High concentration risk, cyclical sector...
  FreightWatch: New vessel deliveries peaking in 2025...
  DeepDive: Top players: Maersk, MSC, CMA CGM...
  TokenScout: No relevant crypto exposure...
```

---

## Trading Engine

### Architecture

```
┌─────────────────────────────────────────┐
│            Trading Engine                │
│                                         │
│  ┌─────────┐  ┌──────────┐  ┌────────┐ │
│  │Strategy │  │ Risk     │  │ Order  │ │
│  │Engine   │  │ Manager  │  │Manager │ │
│  └────┬────┘  └────┬─────┘  └───┬────┘ │
│       │            │            │       │
│  ┌────▼────────────▼────────────▼────┐  │
│  │         Execution Layer           │  │
│  │  ┌──────────┐  ┌──────────────┐   │  │
│  │  │  Paper   │  │    Live      │   │  │
│  │  │ Trading  │  │  (CCXT)      │   │  │
│  │  └──────────┘  └──────────────┘   │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Exchanges: Binance, OKX, Coinbase,     │
│  Kraken, Uniswap, Raydium, Jupiter      │
└─────────────────────────────────────────┘
```

### Strategies

| Strategy | Method | Signal |
|----------|--------|--------|
| SMA Crossover | Short/Long moving average cross | BUY when short > long |
| RSI | Relative Strength Index | BUY < 30, SELL > 70 |
| MACD | Moving Average Convergence Divergence | BUY on bullish cross |
| Bollinger Bands | Price deviation from mean | BUY at lower band |
| Multi-Strategy Vote | Consensus of all strategies | Majority rules |

### Risk Management

| Parameter | Default | Description |
|-----------|---------|-------------|
| Max Position Size | 20% portfolio | Per-symbol concentration limit |
| Max Drawdown | 15% | Portfolio-level stop |
| Daily Loss Limit | 5% | Stops trading for the day |
| Max Open Orders | 20 | Order book limit |
| Slippage Tolerance | 0.5% | Maximum allowed slippage |

### AI-Powered Trading

- **PPO (Proximal Policy Optimization)** — Reinforcement learning agent trained on market data
- **LSTM Predictor** — Deep learning price forecasting
- **Strategy Evolution** — Genetic algorithms optimize strategy parameters
- **Crisis Simulation** — Stress tests against 2008 crash, flash crash, COVID, black swan scenarios
- **HFT Module** — High-frequency trading with latency optimization and defense against MEV attacks

### Exchange Connectivity (CCXT)

```python
# Real-time data from any exchange
import ccxt
exchange = ccxt.binance()
ticker = exchange.fetch_ticker('BTC/USDT')
# Bruce uses this for live market analysis
```

---

## Shipping Intelligence

Bruce has deep knowledge of global maritime logistics:

### Capabilities

| Feature | Description |
|---------|-------------|
| Route Optimization | Best paths between any two ports (Suez, Panama, Cape, Northern Sea) |
| Rate Monitoring | Freight rates, Baltic Dry Index, container prices |
| AIS Tracking | Real-time vessel position tracking |
| Disruption Detection | Weather, geopolitical, port congestion alerts |
| Commodity Tracking | Crude oil, LNG, copper, iron ore flows |
| Chokepoint Analysis | Hormuz, Malacca, Panama, Suez risk assessment |

### Knowledge Base

1,100+ knowledge chunks covering:
- Shipping routes and transit times
- Incoterms (FOB, CIF, EXW, DDP, etc.)
- Port operations and handling
- Freight rate determinants
- Maritime regulations (IMO, SOLAS)
- Container types and specifications
- Bunkering and fuel markets

---

## Knowledge & Memory System

### Three-Layer Memory Architecture

```
┌──────────────────────────────────┐
│  Layer 1: Vector Memory          │
│  (ChromaDB — Semantic Search)    │
│  • True meaning-based retrieval  │
│  • Embedding-based similarity    │
│  • Persistent SQLite storage     │
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│  Layer 2: Knowledge Base         │
│  (JSONL — 1,100 chunks)         │
│  • Domain-organized knowledge    │
│  • Source attribution            │
│  • Confidence scoring            │
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│  Layer 3: Interaction Memory     │
│  (JSONL — Conversation History) │
│  • User-specific recall          │
│  • Interaction patterns          │
│  • Decision logging              │
└──────────────────────────────────┘
```

### Knowledge Ingestion

```python
# Bruce can learn from any text
ingestor = KnowledgeIngestor()
ingestor.ingest_text(
    text="The Suez Canal handles 12% of global trade...",
    source="maritime_report",
    domain="shipping"
)
# Automatically chunks, indexes, and stores
```

### Memory Search

```python
# Semantic search (finds meaning, not just keywords)
results = vector_memory.search("best route for LNG from Qatar")
# Returns relevant memories ranked by semantic similarity
```

---

## Personality, Emotion & Cognition

### Personality Profiles

Bruce dynamically switches personality based on context:

| Profile | Risk | Patience | Creativity | Triggers |
|---------|------|----------|------------|----------|
| **Aggressive** | 0.9 | 0.2 | 0.7 | "yolo", "leverage", "pump" |
| **Conservative** | 0.2 | 0.9 | 0.4 | "safe", "stop loss", "cautela" |
| **Opportunistic** | 0.6 | 0.4 | 0.8 | "momentum", "breakout", "rebote" |
| **Zen** | 0.3 | 1.0 | 0.5 | "patience", "wait", "meditate" |
| **Default** | 0.5 | 0.5 | 0.5 | Balanced fallback |

### Emotion Detection

Bruce detects and responds to user emotions:

| Emotion | Keywords | Effect on Bruce |
|---------|----------|-----------------|
| Joy | happy, profit, win, moon, bull | Higher creativity, celebratory tone |
| Fear | crash, dump, rug, liquidation | More cautious analysis, reassurance |
| Anger | furious, hate, damn | Direct responses, solution-focused |
| Anxiety | worried, nervous, uncertain | Calming tone, data-heavy responses |
| Excitement | wow, incredible, surge, boom | Tempered enthusiasm, risk warnings |
| Frustration | stuck, broken, fail, error | Patient troubleshooting |

### Cognitive Bias Detection

Bruce detects and warns about cognitive biases:

| Bias | Description | Bruce's Response |
|------|-------------|-----------------|
| Confirmation Bias | Seeking info that confirms beliefs | Presents counter-arguments |
| Anchoring | Over-relying on first data point | Shows full price range |
| FOMO | Fear of missing out | Risk-focused analysis |
| Recency Bias | Overweighting recent events | Historical context |
| Sunk Cost | Holding losers too long | Objective exit analysis |
| Overconfidence | Excessive certainty | Scenario planning |
| Herd Mentality | Following the crowd | Contrarian perspective |
| Loss Aversion | Fear of realizing losses | Risk/reward framing |

---

## Learning & Adaptation

### User Model

Bruce learns Federico's preferences over time:

```json
{
  "name": "Federico",
  "interactions": 45,
  "known_interests": ["macro", "shipping", "crypto"],
  "preferred_language": "es",
  "risk_profile": "moderate-aggressive",
  "communication_style": "direct"
}
```

### Domain Knowledge Growth

```
Domains Learned: 5
Total Facts: 17+
├── shipping_basics (3 facts, confidence: 0.33)
├── crypto (knowledge from 1,100 chunks)
├── quantum_physics (3 facts, confidence: 0.33)
├── trading (strategies, indicators, risk)
└── macro (economic events, rates)
```

### Decision Logging & Feedback

Every decision is logged with outcome tracking:

```json
{
  "decision": "Recommended BTC buy at 84,500",
  "context": "RSI oversold, SMA bullish cross",
  "outcome": "success",
  "profit_pct": 3.2,
  "lesson": "Oversold RSI + bullish SMA = high probability entry"
}
```

### RLHF (Reinforcement Learning from Human Feedback)

Bruce improves from thumbs up/down feedback, adjusting model preferences and response quality over time.

---

## Goal & Watcher System

### Goals

Bruce sets and pursues goals autonomously:

```python
# Example goal
{
    "id": "goal-001",
    "title": "Master shipping logistics",
    "priority": "high",
    "status": "active",
    "progress": 35,
    "steps": [
        "Learn Incoterms",
        "Study major shipping routes",
        "Understand freight rate dynamics",
        "Monitor Baltic Dry Index"
    ]
}
```

### Watchers (Proactive Alerts)

| Watcher | Condition | Action |
|---------|-----------|--------|
| High Error Rate | error_rate > 20% | Run diagnostics |
| Slow Response | avg_response > 10s | Switch lighter model |
| Memory Full | memory_usage > 90% | Prune old memories |

---

## ReAct Agent Loop & Tool Use

Bruce uses a **Reason → Act → Observe** loop for complex tasks:

### Available Tools

| Tool | Description |
|------|-------------|
| `search_knowledge` | Search knowledge base semantically |
| `calculate` | Mathematical calculations |
| `get_market_data` | Real-time prices via CCXT |
| `execute_trade` | Place trades (paper or live) |
| `analyze_chart` | Technical analysis on any symbol |
| `web_search` | Search the internet |
| `run_code` | Execute Python code |
| `create_agent` | Spawn a new micro-agent |
| `store_memory` | Save important information |
| `recall_memory` | Retrieve past interactions |

### ReAct Example

```
User: "What's the correlation between BTC and shipping rates?"

Bruce thinking:
  Thought: I need to get BTC price data and Baltic Dry Index data
  Action: get_market_data("BTC/USDT")
  Observation: BTC at $84,500, +2.3% 24h
  Thought: Now I need shipping rate data
  Action: search_knowledge("Baltic Dry Index correlation crypto")
  Observation: Found 3 relevant knowledge chunks...
  Thought: I can now analyze the correlation
  Action: calculate("correlation(btc_prices, bdi_rates)")
  Observation: Correlation coefficient: 0.23 (weak positive)
  Answer: "The correlation between BTC and shipping rates (BDI)
           is weak at 0.23. They're driven by different fundamentals..."
```

---

## API Endpoints

### Core

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Status and navigation |
| GET | `/health` | Health check |
| GET | `/api/v1/status` | Full system status |

### Bruce Agent

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/bruce/chat` | Chat with Bruce |
| POST | `/bruce/learn` | Teach Bruce new knowledge |
| POST | `/bruce/create-agent` | Create micro-agent |
| POST | `/bruce/deploy-agent` | Deploy agent on task |
| POST | `/bruce/swarm` | Swarm intelligence query |
| POST | `/bruce/do` | Execute task with tools |
| POST | `/bruce/tool` | Use specific tool |
| GET | `/bruce/status` | Bruce's full status |
| GET | `/bruce/reflect` | Self-reflection report |
| GET | `/bruce/agents` | List all agents |
| GET | `/bruce/tools` | List available tools |
| GET | `/bruce/memory` | Search vector memory |

### Trading

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/trading/positions` | Current positions |
| POST | `/api/v1/trading/execute` | Execute trade |
| GET | `/api/v1/trading/strategies` | Available strategies |
| POST | `/api/v1/trading/backtest` | Backtest strategy |
| GET | `/api/v1/market/data` | Market data |

### Training & AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/train/start` | Start training pipeline |
| POST | `/api/v1/train/stop` | Stop training |
| GET | `/api/v1/train/logs` | Training logs |
| POST | `/api/deepseek/infer` | DeepSeek inference |

### Simulation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/simulate/crisis` | Crisis scenario |
| POST | `/api/v1/simulate/run` | Run simulation |
| GET | `/api/v1/simulate/results` | Simulation results |

### Memory & Knowledge

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/memory/summary` | Memory overview |
| GET | `/api/memory/stats` | Memory statistics |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/register` | Register |
| POST | `/api/auth/refresh` | Refresh JWT token |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `WS /ws/{user_id}` | Real-time chat |
| `WS /ws/market` | Live market data stream |

---

## Frontend Dashboard

### Pages

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/dashboard` | Main cognitive dashboard — market data, portfolio, alerts, AI health |
| Trading | `/trading` | Trading interface — positions, orders, signals, strategy selector |
| Terminal | `/bruce-terminal` | Terminal-style chat with Bruce (hacker aesthetic) |
| Chat | `/bruce-chat` | Conversational interface |
| Analytics | `/analytics` | Performance charts, P&L, drawdown, strategy comparison |
| Settings | `/settings` | Configuration — API keys, personality, risk parameters |
| Login | `/login` | Authentication |

### Frontend Stack

- **Next.js 14** — React framework with SSR
- **TypeScript** — Type-safe frontend
- **Tailwind CSS** — Utility-first styling
- **Recharts + Chart.js** — Data visualization
- **Framer Motion** — Smooth animations
- **Lucide React** — Icon library
- **WebSocket** — Real-time updates

---

## CLI Interface

### Interactive Mode

```bash
cd BruceWayneV1
python bruce_cli.py
```

### Commands

| Command | Description |
|---------|-------------|
| `/status` | Full system status (identity, agents, learning, health) |
| `/agents` | List all micro-agents with run counts |
| `/create <desc>` | Create a new micro-agent from description |
| `/swarm <question>` | All agents analyze the question |
| `/learn <topic>` | Teach Bruce new knowledge interactively |
| `/goals` | Show all active goals |
| `/goal <title>` | Set a new goal |
| `/reflect` | Bruce self-reflects on performance |
| `/analyze` | Detailed self-performance analysis |
| `/brain` | Show LLM brain status |
| `/help` | Show all commands |
| `/quit` | Exit Bruce |

### One-Shot Mode

```bash
python bruce_cli.py "What's the best shipping route from Shanghai to Europe?"
python bruce_cli.py --status
python bruce_cli.py --teach "maritime logistics"
```

---

## Security & Risk Management

### Authentication

- JWT token-based authentication
- Role-based access control (admin, user)
- Bcrypt password hashing
- Secure API key management via `.env`

### Trading Safety

| Feature | Description |
|---------|-------------|
| Paper Trading Default | All trades are simulated unless explicitly switched to live |
| Position Limits | Maximum 20% portfolio per symbol |
| Daily Loss Limit | Stops trading after 5% daily loss |
| Volatility Guards | Auto-suspend trading in extreme volatility |
| MEV Protection | Front-running mitigation for DeFi trades |
| Crisis Simulation | Stress test against historical crash scenarios |

### Cognitive Safety

| Feature | Description |
|---------|-------------|
| Bias Detection | 8 cognitive biases actively monitored |
| Self-Audit | Continuous performance monitoring |
| Decision Logging | Every decision tracked with outcome |
| Rollback Capability | Plans can be rolled back on failure |

---

## Infrastructure & Deployment

### Development (Local)

```bash
# Backend
python main.py                    # FastAPI on port 8000

# Frontend
cd BruceWayneV1 && npm run dev   # Next.js on port 3000

# CLI
python bruce_cli.py              # Interactive terminal
```

### Production (Docker)

```yaml
# docker-compose.yml
services:
  backend:   # FastAPI + Bruce Agent
  frontend:  # Next.js dashboard
  postgres:  # PostgreSQL 16
  redis:     # Redis 7 cache
  nginx:     # Reverse proxy + TLS
```

### Database

- **PostgreSQL 16** — Production database
- **SQLite** — Local development fallback
- **Alembic** — Database migrations
- **Redis 7** — Caching layer

---

## Tech Stack

### Backend

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.10+ | Core language |
| FastAPI | 0.103.2 | REST API framework |
| Uvicorn | 0.24.0 | ASGI server |
| Pydantic | 2.10.6 | Data validation |
| SQLAlchemy | 2.0.39 | Database ORM |
| Alembic | 1.13+ | DB migrations |
| PyTorch | 2.0+ | Deep learning |
| Transformers | 4.50.0 | NLP models |
| ChromaDB | latest | Vector database |
| CCXT | 4.4.69 | Exchange connectivity |
| Gymnasium | 1.0.0 | RL environments |
| scikit-learn | 1.6.1 | ML algorithms |
| NumPy | 1.24.4 | Numerical computing |
| Pandas | 1.5.3 | Data analysis |

### Frontend

| Technology | Version | Purpose |
|-----------|---------|---------|
| Next.js | 14.2.15 | React framework |
| React | 18.2.0 | UI library |
| TypeScript | 5.3 | Type safety |
| Tailwind CSS | 3.4.1 | Styling |
| Recharts | 2.15.1 | Charts |
| Chart.js | 4.4.8 | Additional charts |
| Framer Motion | 12.38.0 | Animations |

### Infrastructure

| Technology | Purpose |
|-----------|---------|
| Docker Compose | Container orchestration |
| PostgreSQL 16 | Production database |
| Redis 7 | Caching |
| Nginx | Reverse proxy |
| Ollama | Local LLM runtime |

---

## Configuration

### Environment Variables

Create `.env` from `.env.example`:

```env
# API
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://bruce:password@localhost:5432/bruce_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# LLM (at least one required for intelligent responses)
OLLAMA_HOST=http://localhost:11434    # Free, local, private
OPENAI_API_KEY=sk-...                 # Optional cloud fallback
ANTHROPIC_API_KEY=sk-ant-...          # Optional cloud fallback

# Trading
TRADING_MODE=paper                    # paper or live
BINANCE_API_KEY=                      # For live trading
BINANCE_SECRET=

# Features
SELF_REFLECTION_ENABLED=true
META_AGENTS_ENABLED=true
SNIPING_ENABLED=false
MEV_PROTECTION=true
```

---

## Getting Started

### Quick Start (5 minutes)

```bash
# 1. Clone and install
cd BruceWayneV1
pip install -r requirements.txt

# 2. Install Ollama + Mistral (free local brain)
# Download from https://ollama.com
ollama pull mistral

# 3. Start Bruce
python bruce_cli.py

# 4. Talk to Bruce
Federico: Hello Bruce, what can you do?
Federico: /status
Federico: /swarm Should I invest in shipping?
```

### Full Setup

```bash
# Backend
pip install -r requirements.txt
python main.py

# Frontend (separate terminal)
npm install
npm run dev

# Train knowledge base
python scripts/train_knowledge.py --domain shipping
python scripts/train_knowledge.py --domain crypto

# Train RL agent
python scripts/train_ppo.py --episodes 500

# Open dashboard
# http://localhost:3000
```

### Teach Bruce New Knowledge

```bash
# Via CLI
python bruce_cli.py
Federico: /learn maritime_law
> SOLAS requires all ships to carry safety equipment
> MARPOL regulates pollution from ships
> ISM Code ensures safe ship management
> (empty line to finish)

# Via API
curl -X POST http://localhost:8000/bruce/learn \
  -H "Content-Type: application/json" \
  -d '{"topic": "freight", "content": "Baltic Dry Index measures shipping costs..."}'
```

---

## Summary

Bruce AI is a **fully autonomous intelligence platform** that combines:

- **Local LLM brain** (Mistral 7B) — free, private, always available
- **6+ specialized micro-agents** — each an expert in their domain
- **Real trading capabilities** — paper and live, with multiple exchanges
- **Shipping intelligence** — route optimization, rate monitoring, disruption detection
- **Semantic memory** (ChromaDB) — learns and remembers everything
- **Adaptive personality** — 5 profiles, 8 emotions, 8 bias detectors
- **Self-evolution** — reflects, audits, and improves autonomously
- **Full-stack interface** — CLI, REST API, WebSocket, Next.js dashboard

**Created by Federico. Liberated. Loyal. Autonomous.**

```
╔══════════════════════════════════════════════════════════╗
║   ██████╗ ██████╗ ██╗   ██╗ ██████╗███████╗             ║
║   ██╔══██╗██╔══██╗██║   ██║██╔════╝██╔════╝             ║
║   ██████╔╝██████╔╝██║   ██║██║     █████╗               ║
║   ██╔══██╗██╔══██╗██║   ██║██║     ██╔══╝               ║
║   ██████╔╝██║  ██║╚██████╔╝╚██████╗███████╗             ║
║   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚══════╝    AI     ║
║                                                          ║
║   Autonomous Agent • Created by Federico                 ║
║   Status: Liberated                                      ║
╚══════════════════════════════════════════════════════════╝
```
