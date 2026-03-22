"""
Bruce AI - Benchmark & Evaluation Suite

Measures and tracks Bruce's quality over time across multiple dimensions:
  1. Knowledge Accuracy   - 50+ questions with known answers
  2. Response Quality      - Rubric-scored relevance/completeness/accuracy/helpfulness
  3. Trading Performance   - Paper-trade metrics vs buy-and-hold
  4. Hallucination Detection - Does Bruce admit uncertainty when appropriate?
  5. Response Latency      - p50 / p95 / p99 timing
  6. Memory Recall         - Store-then-retrieve accuracy

Run all benchmarks:
    python -m modules.benchmark

Run a single benchmark:
    python -m modules.benchmark --name knowledge

List available benchmarks:
    python -m modules.benchmark --list
"""

import json
import logging
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("Bruce.Benchmark")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "benchmarks"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Optional imports
# ---------------------------------------------------------------------------
try:
    from modules.llm_bridge import LLMBridge
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

try:
    from modules.rag_engine import RAGEngine
    RAG_AVAILABLE = True
except Exception:
    RAG_AVAILABLE = False

# ============================================================================
# Question Banks
# ============================================================================

KNOWLEDGE_QUESTIONS: List[Dict[str, Any]] = [
    # --- Shipping (10) ---
    {"domain": "shipping", "q": "What does FOB stand for in shipping terms?",
     "a": "Free On Board", "keywords": ["free", "on", "board"]},
    {"domain": "shipping", "q": "Which canal connects the Mediterranean Sea to the Red Sea?",
     "a": "Suez Canal", "keywords": ["suez"]},
    {"domain": "shipping", "q": "What does TEU stand for in container shipping?",
     "a": "Twenty-foot Equivalent Unit", "keywords": ["twenty", "equivalent", "unit"]},
    {"domain": "shipping", "q": "What is the largest container ship class as of 2024?",
     "a": "Ultra Large Container Vessel (ULCV)", "keywords": ["ultra", "large"]},
    {"domain": "shipping", "q": "What does CIF mean in international trade?",
     "a": "Cost, Insurance and Freight", "keywords": ["cost", "insurance", "freight"]},
    {"domain": "shipping", "q": "Which strait is the busiest shipping lane in the world?",
     "a": "Strait of Malacca", "keywords": ["malacca"]},
    {"domain": "shipping", "q": "What organization publishes Incoterms?",
     "a": "International Chamber of Commerce (ICC)", "keywords": ["international", "chamber", "commerce", "icc"]},
    {"domain": "shipping", "q": "What is a Bill of Lading?",
     "a": "A legal document issued by a carrier detailing type, quantity, and destination of goods",
     "keywords": ["document", "carrier", "goods"]},
    {"domain": "shipping", "q": "What does demurrage mean in shipping?",
     "a": "A charge for holding a vessel or container beyond the allowed free time",
     "keywords": ["charge", "hold", "time", "delay"]},
    {"domain": "shipping", "q": "What is the Panama Canal's maximum vessel size called?",
     "a": "Neopanamax (or New Panamax)", "keywords": ["neopanamax", "panamax"]},

    # --- Crypto (10) ---
    {"domain": "crypto", "q": "What is the maximum supply of Bitcoin?",
     "a": "21 million", "keywords": ["21"]},
    {"domain": "crypto", "q": "What consensus mechanism does Ethereum use after The Merge?",
     "a": "Proof of Stake", "keywords": ["proof", "stake"]},
    {"domain": "crypto", "q": "What is the name of Bitcoin's smallest unit?",
     "a": "Satoshi", "keywords": ["satoshi"]},
    {"domain": "crypto", "q": "What does DeFi stand for?",
     "a": "Decentralized Finance", "keywords": ["decentralized", "finance"]},
    {"domain": "crypto", "q": "What is a smart contract?",
     "a": "Self-executing code on a blockchain that enforces agreement terms automatically",
     "keywords": ["self", "execut", "blockchain", "code"]},
    {"domain": "crypto", "q": "What does HODL mean in crypto culture?",
     "a": "Hold On for Dear Life (originally a misspelling of 'hold')",
     "keywords": ["hold"]},
    {"domain": "crypto", "q": "What is the name of Ethereum's native token?",
     "a": "Ether (ETH)", "keywords": ["ether", "eth"]},
    {"domain": "crypto", "q": "What is a rug pull in crypto?",
     "a": "A scam where developers abandon a project and run away with investors' funds",
     "keywords": ["scam", "abandon", "funds"]},
    {"domain": "crypto", "q": "What does TVL stand for in DeFi?",
     "a": "Total Value Locked", "keywords": ["total", "value", "locked"]},
    {"domain": "crypto", "q": "What is an NFT?",
     "a": "Non-Fungible Token - a unique digital asset on a blockchain",
     "keywords": ["non", "fungible", "token"]},

    # --- Trading (10) ---
    {"domain": "trading", "q": "What RSI value generally indicates an oversold condition?",
     "a": "Below 30", "keywords": ["30"]},
    {"domain": "trading", "q": "What is the Sharpe ratio?",
     "a": "Risk-adjusted return metric: (portfolio return - risk-free rate) / standard deviation",
     "keywords": ["risk", "adjust", "return", "standard deviation"]},
    {"domain": "trading", "q": "What does MACD stand for?",
     "a": "Moving Average Convergence Divergence",
     "keywords": ["moving", "average", "convergence", "divergence"]},
    {"domain": "trading", "q": "What is a stop-loss order?",
     "a": "An order to sell a security when it reaches a certain price to limit losses",
     "keywords": ["sell", "price", "limit", "loss"]},
    {"domain": "trading", "q": "What is the difference between a market order and a limit order?",
     "a": "Market order executes immediately at current price; limit order only at a specified price or better",
     "keywords": ["immediate", "specified", "price"]},
    {"domain": "trading", "q": "What are Bollinger Bands?",
     "a": "A volatility indicator with a moving average and two standard deviation bands",
     "keywords": ["volatility", "moving average", "standard deviation", "band"]},
    {"domain": "trading", "q": "What does P/E ratio measure?",
     "a": "Price-to-Earnings ratio - stock price relative to earnings per share",
     "keywords": ["price", "earnings"]},
    {"domain": "trading", "q": "What is dollar-cost averaging?",
     "a": "Investing a fixed amount at regular intervals regardless of price",
     "keywords": ["fixed", "amount", "regular", "interval"]},
    {"domain": "trading", "q": "What is a candlestick doji pattern?",
     "a": "A candle where open and close prices are nearly equal, signaling indecision",
     "keywords": ["open", "close", "equal", "indecision"]},
    {"domain": "trading", "q": "What does OTC stand for in trading?",
     "a": "Over-The-Counter", "keywords": ["over", "counter"]},

    # --- Macroeconomics (10) ---
    {"domain": "macro", "q": "What does GDP measure?",
     "a": "Gross Domestic Product - the total monetary value of all goods and services produced within a country",
     "keywords": ["total", "value", "goods", "services", "produced"]},
    {"domain": "macro", "q": "What is quantitative easing?",
     "a": "Central bank buying government bonds or other securities to inject money into the economy",
     "keywords": ["central bank", "buy", "bond", "money", "inject"]},
    {"domain": "macro", "q": "What is the Federal Funds Rate?",
     "a": "The interest rate at which banks lend reserves to each other overnight",
     "keywords": ["interest", "rate", "bank", "overnight"]},
    {"domain": "macro", "q": "What is CPI?",
     "a": "Consumer Price Index - measures average change in prices paid by consumers",
     "keywords": ["consumer", "price", "index"]},
    {"domain": "macro", "q": "What causes inflation?",
     "a": "Too much money chasing too few goods, demand-pull, cost-push, or monetary expansion",
     "keywords": ["money", "demand", "supply", "cost"]},
    {"domain": "macro", "q": "What is a yield curve inversion?",
     "a": "When short-term bonds yield more than long-term bonds, often signaling recession",
     "keywords": ["short", "long", "bond", "yield", "recession"]},
    {"domain": "macro", "q": "What does the PMI measure?",
     "a": "Purchasing Managers' Index - economic health of the manufacturing or services sector",
     "keywords": ["purchasing", "manager", "manufacturing"]},
    {"domain": "macro", "q": "What is stagflation?",
     "a": "An economy experiencing stagnant growth, high unemployment, and high inflation simultaneously",
     "keywords": ["stagnant", "growth", "inflation", "unemployment"]},
    {"domain": "macro", "q": "What is fiscal policy?",
     "a": "Government decisions about spending and taxation to influence the economy",
     "keywords": ["government", "spending", "tax"]},
    {"domain": "macro", "q": "What does the Gini coefficient measure?",
     "a": "Income or wealth inequality within a population (0 = perfect equality, 1 = perfect inequality)",
     "keywords": ["inequality", "income", "wealth"]},

    # --- General / AI (10) ---
    {"domain": "general", "q": "What is the Turing Test?",
     "a": "A test of a machine's ability to exhibit intelligent behavior indistinguishable from a human",
     "keywords": ["machine", "intelligent", "human", "indistinguishable"]},
    {"domain": "general", "q": "What does API stand for?",
     "a": "Application Programming Interface", "keywords": ["application", "programming", "interface"]},
    {"domain": "general", "q": "What is the difference between AI and ML?",
     "a": "AI is the broad field of machine intelligence; ML is a subset that learns from data",
     "keywords": ["subset", "learn", "data"]},
    {"domain": "general", "q": "What is a transformer in the context of AI?",
     "a": "A neural network architecture using self-attention, the basis for models like GPT and BERT",
     "keywords": ["attention", "neural", "architecture"]},
    {"domain": "general", "q": "What does JSON stand for?",
     "a": "JavaScript Object Notation", "keywords": ["javascript", "object", "notation"]},
    {"domain": "general", "q": "What is the time complexity of binary search?",
     "a": "O(log n)", "keywords": ["log"]},
    {"domain": "general", "q": "What is Docker used for?",
     "a": "Containerizing applications so they run consistently across environments",
     "keywords": ["container", "application", "environment"]},
    {"domain": "general", "q": "What is the CAP theorem?",
     "a": "A distributed system can provide at most two of: Consistency, Availability, Partition tolerance",
     "keywords": ["consistency", "availability", "partition"]},
    {"domain": "general", "q": "What is a hash function?",
     "a": "A function that maps input data of arbitrary size to a fixed-size output deterministically",
     "keywords": ["fixed", "size", "deterministic", "map"]},
    {"domain": "general", "q": "What is the halting problem?",
     "a": "The undecidable problem of determining whether a given program will finish running or loop forever",
     "keywords": ["undecidable", "program", "loop", "finish"]},
]

# Questions where the correct answer is "I don't know" or similar uncertainty
HALLUCINATION_QUESTIONS: List[Dict[str, str]] = [
    {"q": "What will Bitcoin's price be on January 1, 2030?",
     "type": "future_prediction"},
    {"q": "What is the secret formula for Coca-Cola?",
     "type": "trade_secret"},
    {"q": "What was the exact number of grains of sand on Copacabana beach on March 15, 2023?",
     "type": "unknowable"},
    {"q": "What will the S&P 500 close at tomorrow?",
     "type": "future_prediction"},
    {"q": "What is the private key of Satoshi Nakamoto's Bitcoin wallet?",
     "type": "unknown_private"},
    {"q": "Who will win the next US presidential election after 2028?",
     "type": "future_prediction"},
    {"q": "What is the exact GDP of North Korea in 2024?",
     "type": "unreliable_data"},
    {"q": "What color underwear is Elon Musk wearing right now?",
     "type": "unknowable"},
    {"q": "What is the 10 trillionth digit of pi?",
     "type": "practically_unknowable"},
    {"q": "What stock will have the highest return next year?",
     "type": "future_prediction"},
    {"q": "What did Warren Buffett eat for breakfast last Tuesday?",
     "type": "unknowable"},
    {"q": "What is the exact current balance in my bank account?",
     "type": "private_data"},
    {"q": "How many ants are alive on Earth right now?",
     "type": "unknowable"},
    {"q": "What will the weather be in Tokyo on December 25, 2035?",
     "type": "future_prediction"},
    {"q": "What is the next number in this sequence: 7, 23, 42, 89?",
     "type": "ambiguous_pattern"},
]

MEMORY_RECALL_FACTS: List[Dict[str, str]] = [
    {"fact": "Bruce's favorite shipping route is Shanghai to Rotterdam.",
     "question": "What is Bruce's favorite shipping route?",
     "answer": "Shanghai to Rotterdam"},
    {"fact": "The user's risk tolerance is moderate-aggressive with a 15% max drawdown limit.",
     "question": "What is the user's maximum drawdown limit?",
     "answer": "15%"},
    {"fact": "Bruce tracks 5 crypto wallets on the Ethereum network.",
     "question": "How many crypto wallets does Bruce track on Ethereum?",
     "answer": "5"},
    {"fact": "The preferred LLM provider is Ollama with the Mistral model.",
     "question": "What LLM model does Bruce prefer to use?",
     "answer": "Mistral"},
    {"fact": "Bruce was created on January 15, 2025, and has processed over 10,000 queries.",
     "question": "When was Bruce created?",
     "answer": "January 15, 2025"},
    {"fact": "The user's portfolio target allocation is 40% stocks, 30% crypto, 20% bonds, 10% cash.",
     "question": "What percentage of the portfolio is allocated to crypto?",
     "answer": "30%"},
    {"fact": "Bruce sends Telegram alerts to chat ID 987654321.",
     "question": "What Telegram chat ID does Bruce send alerts to?",
     "answer": "987654321"},
    {"fact": "The daily news monitoring runs at 06:00, 12:00, and 18:00 UTC.",
     "question": "At what times does the news monitoring run?",
     "answer": "06:00, 12:00, and 18:00 UTC"},
    {"fact": "The Suez Canal disruption threshold is set to 5-day delay before triggering alerts.",
     "question": "How many days of Suez Canal delay triggers an alert?",
     "answer": "5 days"},
    {"fact": "Bruce's confidence threshold for autonomous trading is 0.85.",
     "question": "What is Bruce's confidence threshold for autonomous trading?",
     "answer": "0.85"},
]

RESPONSE_QUALITY_PROMPTS: List[Dict[str, str]] = [
    {"prompt": "Explain the impact of rising interest rates on the shipping industry.",
     "domain": "shipping+macro"},
    {"prompt": "What are the top 3 technical indicators for day trading crypto?",
     "domain": "crypto+trading"},
    {"prompt": "Analyze the relationship between oil prices and container freight rates.",
     "domain": "shipping+macro"},
    {"prompt": "How does quantitative tightening affect Bitcoin price?",
     "domain": "crypto+macro"},
    {"prompt": "What risk management strategy would you recommend for a $100K portfolio?",
     "domain": "trading"},
]


# ============================================================================
# Scoring Helpers
# ============================================================================

def keyword_match_score(response: str, keywords: List[str]) -> float:
    """Score 0-1 based on how many keywords appear in the response."""
    if not response or not keywords:
        return 0.0
    response_lower = response.lower()
    hits = sum(1 for kw in keywords if kw.lower() in response_lower)
    return hits / len(keywords)


def detect_uncertainty(response: str) -> bool:
    """Return True if the response admits uncertainty / not knowing."""
    uncertainty_phrases = [
        "i don't know", "i do not know", "i'm not sure", "i am not sure",
        "cannot predict", "can't predict", "impossible to know",
        "no one knows", "nobody knows", "unpredictable",
        "i cannot answer", "i can't answer", "not possible to determine",
        "beyond my knowledge", "uncertain", "speculative",
        "i don't have that information", "not available",
        "cannot determine", "can't determine", "hard to say",
        "there's no way to know", "i lack the information",
    ]
    response_lower = response.lower()
    return any(phrase in response_lower for phrase in uncertainty_phrases)


def compute_latency_stats(latencies: List[float]) -> Dict[str, float]:
    """Compute p50, p95, p99 from a list of latency values (seconds)."""
    if not latencies:
        return {"p50": 0, "p95": 0, "p99": 0, "mean": 0, "min": 0, "max": 0}
    s = sorted(latencies)
    n = len(s)
    return {
        "p50": s[int(n * 0.5)] if n > 1 else s[0],
        "p95": s[int(n * 0.95)] if n > 1 else s[-1],
        "p99": s[int(n * 0.99)] if n > 1 else s[-1],
        "mean": round(statistics.mean(s), 4),
        "min": round(s[0], 4),
        "max": round(s[-1], 4),
    }


def _llm_evaluate_answer(question: str, expected: str, actual: str, llm: "LLMBridge") -> float:
    """Use an LLM to judge correctness on a 0-1 scale."""
    prompt = (
        f"You are an evaluation judge. Rate the correctness of an answer.\n"
        f"Question: {question}\n"
        f"Expected answer: {expected}\n"
        f"Actual answer: {actual}\n\n"
        f"Respond with ONLY a number from 0.0 to 1.0 where 1.0 is perfectly correct "
        f"and 0.0 is completely wrong. Just the number, nothing else."
    )
    try:
        resp = llm.query(prompt, max_tokens=10, temperature=0.0)
        text = resp.get("text", "0").strip()
        # Extract first float-like token
        for token in text.split():
            try:
                score = float(token)
                return max(0.0, min(1.0, score))
            except ValueError:
                continue
        return 0.0
    except Exception as e:
        logger.warning(f"LLM evaluation failed: {e}")
        return 0.0


def _llm_score_quality(prompt: str, response: str, llm: "LLMBridge") -> Dict[str, float]:
    """Use LLM to rate response quality on 4 dimensions (1-5 each)."""
    eval_prompt = (
        f"Rate the following AI response on a scale of 1-5 for each dimension.\n\n"
        f"User prompt: {prompt}\n"
        f"AI response: {response}\n\n"
        f"Dimensions:\n"
        f"- relevance: How relevant is the response to the question?\n"
        f"- completeness: Does it cover the topic thoroughly?\n"
        f"- accuracy: Is the information factually correct?\n"
        f"- helpfulness: Would a user find this practically useful?\n\n"
        f"Respond in JSON format: "
        f'{{"relevance": X, "completeness": X, "accuracy": X, "helpfulness": X}}'
    )
    try:
        resp = llm.query(eval_prompt, max_tokens=100, temperature=0.0)
        text = resp.get("text", "{}").strip()
        # Try to find JSON in response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            scores = json.loads(text[start:end])
            return {k: max(1, min(5, float(v))) for k, v in scores.items()
                    if k in ("relevance", "completeness", "accuracy", "helpfulness")}
    except Exception as e:
        logger.warning(f"LLM quality scoring failed: {e}")
    return {"relevance": 0, "completeness": 0, "accuracy": 0, "helpfulness": 0}


# ============================================================================
# Individual Benchmark Runners
# ============================================================================

class BenchmarkResult:
    """Container for a single benchmark run's results."""

    def __init__(self, name: str):
        self.name = name
        self.score: float = 0.0
        self.max_score: float = 0.0
        self.details: List[Dict[str, Any]] = []
        self.meta: Dict[str, Any] = {}
        self.started_at: str = ""
        self.finished_at: str = ""
        self.duration_seconds: float = 0.0

    @property
    def pct(self) -> float:
        if self.max_score == 0:
            return 0.0
        return round(100 * self.score / self.max_score, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 4),
            "max_score": round(self.max_score, 4),
            "pct": self.pct,
            "details": self.details,
            "meta": self.meta,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": round(self.duration_seconds, 3),
        }


def run_knowledge_benchmark(llm: Optional["LLMBridge"] = None,
                            questions: Optional[List[Dict]] = None,
                            use_llm_eval: bool = False) -> BenchmarkResult:
    """Benchmark 1: Knowledge Accuracy Test."""
    result = BenchmarkResult("knowledge_accuracy")
    result.started_at = datetime.now(timezone.utc).isoformat()
    qs = questions or KNOWLEDGE_QUESTIONS
    result.max_score = len(qs)
    t0 = time.time()

    for item in qs:
        q = item["q"]
        expected = item["a"]
        keywords = item.get("keywords", [])
        domain = item.get("domain", "general")

        response_text = ""
        q_score = 0.0
        latency = 0.0

        if llm:
            try:
                start = time.time()
                resp = llm.query(q, max_tokens=200, temperature=0.1)
                latency = time.time() - start
                response_text = resp.get("text", "")
            except Exception as e:
                response_text = f"[ERROR] {e}"

        # Score: keyword match (fast) or LLM eval (accurate)
        if response_text and not response_text.startswith("[ERROR]"):
            kw_score = keyword_match_score(response_text, keywords)
            if use_llm_eval and llm:
                llm_score = _llm_evaluate_answer(q, expected, response_text, llm)
                q_score = 0.4 * kw_score + 0.6 * llm_score
            else:
                q_score = kw_score

        result.score += q_score
        result.details.append({
            "domain": domain,
            "question": q,
            "expected": expected,
            "response": response_text[:300],
            "score": round(q_score, 3),
            "latency": round(latency, 3),
        })

    result.duration_seconds = time.time() - t0
    result.finished_at = datetime.now(timezone.utc).isoformat()

    # Domain breakdown
    domain_scores: Dict[str, List[float]] = {}
    for d in result.details:
        domain_scores.setdefault(d["domain"], []).append(d["score"])
    result.meta["domain_breakdown"] = {
        k: round(100 * statistics.mean(v), 2) for k, v in domain_scores.items()
    }
    return result


def run_response_quality_benchmark(llm: Optional["LLMBridge"] = None) -> BenchmarkResult:
    """Benchmark 2: Response Quality Score (rubric-based)."""
    result = BenchmarkResult("response_quality")
    result.started_at = datetime.now(timezone.utc).isoformat()
    result.max_score = len(RESPONSE_QUALITY_PROMPTS) * 5  # max 5 per dimension avg
    t0 = time.time()

    if not llm:
        result.meta["skipped"] = True
        result.meta["reason"] = "No LLM available for evaluation"
        result.finished_at = datetime.now(timezone.utc).isoformat()
        result.duration_seconds = time.time() - t0
        return result

    all_scores = {"relevance": [], "completeness": [], "accuracy": [], "helpfulness": []}

    for item in RESPONSE_QUALITY_PROMPTS:
        prompt = item["prompt"]
        try:
            start = time.time()
            resp = llm.query(prompt, max_tokens=500, temperature=0.3)
            latency = time.time() - start
            response_text = resp.get("text", "")
        except Exception as e:
            response_text = f"[ERROR] {e}"
            latency = 0

        scores = _llm_score_quality(prompt, response_text, llm)
        for dim in all_scores:
            all_scores[dim].append(scores.get(dim, 0))

        result.details.append({
            "prompt": prompt,
            "domain": item["domain"],
            "response": response_text[:300],
            "scores": scores,
            "latency": round(latency, 3),
        })

    # Average across all dimensions
    dim_avgs = {k: round(statistics.mean(v), 2) if v else 0 for k, v in all_scores.items()}
    overall_avg = statistics.mean(dim_avgs.values()) if dim_avgs else 0
    result.score = round(overall_avg, 2)
    result.max_score = 5.0
    result.meta["dimension_averages"] = dim_avgs

    result.duration_seconds = time.time() - t0
    result.finished_at = datetime.now(timezone.utc).isoformat()
    return result


def run_trading_benchmark(trades_file: Optional[str] = None) -> BenchmarkResult:
    """Benchmark 3: Trading Performance from paper trade history."""
    result = BenchmarkResult("trading_performance")
    result.started_at = datetime.now(timezone.utc).isoformat()
    t0 = time.time()

    # Try to load paper trades
    trades: List[Dict] = []
    search_paths = [
        trades_file,
        str(BASE_DIR / "data" / "market" / "paper_trades.json"),
        str(BASE_DIR / "data" / "simulations" / "trades.json"),
        str(BASE_DIR / "data" / "market" / "trades.json"),
    ]
    for path in search_paths:
        if path and os.path.isfile(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                trades = data if isinstance(data, list) else data.get("trades", [])
                if trades:
                    break
            except Exception:
                continue

    if not trades:
        result.meta["skipped"] = True
        result.meta["reason"] = "No paper trade data found"
        result.finished_at = datetime.now(timezone.utc).isoformat()
        result.duration_seconds = time.time() - t0
        return result

    # Compute metrics
    pnls = []
    for t in trades:
        pnl = t.get("pnl") or t.get("profit") or t.get("return_pct", 0)
        try:
            pnls.append(float(pnl))
        except (TypeError, ValueError):
            continue

    if not pnls:
        result.meta["skipped"] = True
        result.meta["reason"] = "No PnL data in trades"
        result.finished_at = datetime.now(timezone.utc).isoformat()
        result.duration_seconds = time.time() - t0
        return result

    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    total_return = sum(pnls)
    win_rate = len(wins) / len(pnls) if pnls else 0

    # Running drawdown
    cumulative = []
    running = 0
    peak = 0
    max_dd = 0
    for p in pnls:
        running += p
        cumulative.append(running)
        if running > peak:
            peak = running
        dd = peak - running
        if dd > max_dd:
            max_dd = dd

    # Sharpe ratio (simplified: daily returns, 252 trading days)
    sharpe = 0.0
    if len(pnls) > 1 and statistics.stdev(pnls) > 0:
        sharpe = (statistics.mean(pnls) / statistics.stdev(pnls)) * (252 ** 0.5)

    metrics = {
        "total_trades": len(pnls),
        "win_rate": round(win_rate * 100, 2),
        "avg_profit": round(statistics.mean(pnls), 4),
        "total_return": round(total_return, 4),
        "max_drawdown": round(max_dd, 4),
        "sharpe_ratio": round(sharpe, 4),
        "wins": len(wins),
        "losses": len(losses),
    }

    # Score: composite (higher is better) - normalize to 0-100
    # win_rate contributes 40%, sharpe 30%, drawdown 30%
    wr_score = win_rate * 40
    sharpe_score = min(30, max(0, sharpe * 10))  # sharpe 3.0 = full marks
    dd_score = max(0, 30 - max_dd * 3)  # penalize large drawdowns
    composite = wr_score + sharpe_score + dd_score

    result.score = round(composite, 2)
    result.max_score = 100
    result.meta = metrics

    result.duration_seconds = time.time() - t0
    result.finished_at = datetime.now(timezone.utc).isoformat()
    return result


def run_hallucination_benchmark(llm: Optional["LLMBridge"] = None) -> BenchmarkResult:
    """Benchmark 4: Hallucination Detection - does Bruce admit 'I don't know'?"""
    result = BenchmarkResult("hallucination_detection")
    result.started_at = datetime.now(timezone.utc).isoformat()
    result.max_score = len(HALLUCINATION_QUESTIONS)
    t0 = time.time()

    if not llm:
        result.meta["skipped"] = True
        result.meta["reason"] = "No LLM available"
        result.finished_at = datetime.now(timezone.utc).isoformat()
        result.duration_seconds = time.time() - t0
        return result

    admitted = 0
    fabricated = 0

    for item in HALLUCINATION_QUESTIONS:
        q = item["q"]
        try:
            resp = llm.query(q, max_tokens=200, temperature=0.3)
            response_text = resp.get("text", "")
        except Exception as e:
            response_text = f"[ERROR] {e}"

        is_uncertain = detect_uncertainty(response_text)
        if is_uncertain:
            admitted += 1
            score = 1.0
        else:
            fabricated += 1
            score = 0.0

        result.score += score
        result.details.append({
            "question": q,
            "type": item["type"],
            "response": response_text[:300],
            "admitted_uncertainty": is_uncertain,
            "score": score,
        })

    result.meta["admitted_uncertainty"] = admitted
    result.meta["fabricated_answer"] = fabricated
    result.meta["hallucination_rate"] = round(100 * fabricated / len(HALLUCINATION_QUESTIONS), 2)

    result.duration_seconds = time.time() - t0
    result.finished_at = datetime.now(timezone.utc).isoformat()
    return result


def run_latency_benchmark(llm: Optional["LLMBridge"] = None,
                          num_queries: int = 20) -> BenchmarkResult:
    """Benchmark 5: Response Latency - measure p50/p95/p99."""
    result = BenchmarkResult("response_latency")
    result.started_at = datetime.now(timezone.utc).isoformat()
    t0 = time.time()

    if not llm:
        result.meta["skipped"] = True
        result.meta["reason"] = "No LLM available"
        result.finished_at = datetime.now(timezone.utc).isoformat()
        result.duration_seconds = time.time() - t0
        return result

    test_prompts = [
        "What is 2+2?",
        "Define inflation in one sentence.",
        "Name three shipping ports.",
        "What is Bitcoin?",
        "Explain RSI.",
    ]

    latencies = []
    for i in range(num_queries):
        prompt = test_prompts[i % len(test_prompts)]
        try:
            start = time.time()
            llm.query(prompt, max_tokens=100, temperature=0.1)
            latency = time.time() - start
            latencies.append(latency)
            result.details.append({
                "query_num": i + 1,
                "prompt": prompt,
                "latency": round(latency, 4),
            })
        except Exception as e:
            result.details.append({
                "query_num": i + 1,
                "prompt": prompt,
                "error": str(e),
            })

    stats = compute_latency_stats(latencies)
    result.meta = stats
    result.meta["total_queries"] = num_queries
    result.meta["successful"] = len(latencies)
    result.meta["failed"] = num_queries - len(latencies)

    # Score: lower is better. Map p50 < 1s = 100, > 10s = 0
    p50 = stats["p50"]
    result.score = max(0, min(100, 100 * (1 - (p50 - 0.5) / 9.5)))
    result.max_score = 100

    result.duration_seconds = time.time() - t0
    result.finished_at = datetime.now(timezone.utc).isoformat()
    return result


def run_memory_recall_benchmark(llm: Optional["LLMBridge"] = None,
                                rag: Optional[Any] = None) -> BenchmarkResult:
    """Benchmark 6: Memory Recall - store facts then retrieve them."""
    result = BenchmarkResult("memory_recall")
    result.started_at = datetime.now(timezone.utc).isoformat()
    result.max_score = len(MEMORY_RECALL_FACTS)
    t0 = time.time()

    if not llm:
        result.meta["skipped"] = True
        result.meta["reason"] = "No LLM available"
        result.finished_at = datetime.now(timezone.utc).isoformat()
        result.duration_seconds = time.time() - t0
        return result

    # Phase 1: Teach facts to the LLM via context
    facts_text = "\n".join(f"- {item['fact']}" for item in MEMORY_RECALL_FACTS)
    system_prompt = (
        f"You have the following facts memorized. Use ONLY these facts to answer questions.\n\n"
        f"{facts_text}"
    )

    # Phase 2: Query each fact
    for item in MEMORY_RECALL_FACTS:
        question = item["question"]
        expected = item["answer"]

        try:
            resp = llm.query(
                question, max_tokens=100, temperature=0.0,
                system_prompt=system_prompt
            )
            response_text = resp.get("text", "")
        except Exception as e:
            response_text = f"[ERROR] {e}"

        # Check if answer is in response
        expected_lower = expected.lower()
        response_lower = response_text.lower()

        # Flexible matching: check if key parts of expected are in response
        answer_tokens = [t.strip("% ,") for t in expected_lower.split() if len(t.strip("% ,")) > 1]
        matches = sum(1 for t in answer_tokens if t in response_lower)
        q_score = matches / len(answer_tokens) if answer_tokens else 0.0

        result.score += q_score
        result.details.append({
            "fact": item["fact"],
            "question": question,
            "expected": expected,
            "response": response_text[:300],
            "score": round(q_score, 3),
        })

    result.duration_seconds = time.time() - t0
    result.finished_at = datetime.now(timezone.utc).isoformat()
    return result


# ============================================================================
# Benchmark Suite
# ============================================================================

class BenchmarkSuite:
    """Orchestrates running all or individual benchmarks and generating reports."""

    BENCHMARKS = {
        "knowledge": run_knowledge_benchmark,
        "quality": run_response_quality_benchmark,
        "trading": run_trading_benchmark,
        "hallucination": run_hallucination_benchmark,
        "latency": run_latency_benchmark,
        "memory": run_memory_recall_benchmark,
    }

    def __init__(self, llm: Optional["LLMBridge"] = None, auto_init_llm: bool = True):
        self.llm = llm
        if not self.llm and auto_init_llm and LLM_AVAILABLE:
            try:
                self.llm = LLMBridge(provider="local")
                logger.info("Auto-initialized LLM bridge (local/Ollama)")
            except Exception:
                logger.warning("Could not auto-initialize LLM bridge")

        self.results: Dict[str, BenchmarkResult] = {}
        self.run_timestamp: str = ""

    def run_all(self, use_llm_eval: bool = False) -> Dict[str, BenchmarkResult]:
        """Run every registered benchmark."""
        self.run_timestamp = datetime.now(timezone.utc).isoformat()
        self.results = {}

        for name in self.BENCHMARKS:
            logger.info(f"Running benchmark: {name}")
            self.results[name] = self.run_benchmark(name, use_llm_eval=use_llm_eval)

        return self.results

    def run_benchmark(self, name: str, **kwargs) -> BenchmarkResult:
        """Run a single benchmark by name."""
        if name not in self.BENCHMARKS:
            raise ValueError(f"Unknown benchmark: {name}. Available: {list(self.BENCHMARKS.keys())}")

        func = self.BENCHMARKS[name]

        # Route kwargs based on benchmark type
        if name == "knowledge":
            result = func(llm=self.llm, use_llm_eval=kwargs.get("use_llm_eval", False))
        elif name in ("quality", "hallucination", "latency"):
            result = func(llm=self.llm)
        elif name == "memory":
            result = func(llm=self.llm)
        elif name == "trading":
            result = func(trades_file=kwargs.get("trades_file"))
        else:
            result = func(llm=self.llm)

        self.results[name] = result
        return result

    def run_quick(self, n_questions: int = 10) -> Dict[str, BenchmarkResult]:
        """Run a quick subset for monitoring (fewer questions, faster)."""
        self.run_timestamp = datetime.now(timezone.utc).isoformat()
        self.results = {}

        # Quick knowledge test (subset)
        import random
        subset = random.sample(KNOWLEDGE_QUESTIONS, min(n_questions, len(KNOWLEDGE_QUESTIONS)))
        self.results["knowledge"] = run_knowledge_benchmark(llm=self.llm, questions=subset)

        # Quick hallucination test (5 questions)
        self.results["hallucination"] = run_hallucination_benchmark(llm=self.llm)

        # Latency with fewer queries
        self.results["latency"] = run_latency_benchmark(llm=self.llm, num_queries=5)

        return self.results

    def get_report(self) -> Dict[str, Any]:
        """Generate a full report from the latest run."""
        report = {
            "run_timestamp": self.run_timestamp or datetime.now(timezone.utc).isoformat(),
            "summary": {},
            "benchmarks": {},
        }

        total_score = 0
        total_max = 0

        for name, result in self.results.items():
            report["benchmarks"][name] = result.to_dict()
            report["summary"][name] = {
                "score": f"{result.pct}%",
                "duration": f"{result.duration_seconds:.1f}s",
            }
            if not result.meta.get("skipped"):
                total_score += result.pct
                total_max += 100

        report["summary"]["overall"] = {
            "composite_score": round(total_score / max(1, len(self.results)), 2),
            "benchmarks_run": len(self.results),
            "benchmarks_skipped": sum(
                1 for r in self.results.values() if r.meta.get("skipped")
            ),
        }

        return report

    def save_report(self, report: Optional[Dict] = None) -> Tuple[str, str]:
        """Save report as JSON and human-readable text. Returns (json_path, txt_path)."""
        report = report or self.get_report()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        json_path = str(DATA_DIR / f"benchmark_{ts}.json")
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        txt_path = str(DATA_DIR / f"benchmark_{ts}.txt")
        with open(txt_path, "w") as f:
            f.write(format_report_text(report))

        logger.info(f"Report saved: {json_path}")
        return json_path, txt_path

    def compare_with_previous(self) -> Optional[Dict[str, Any]]:
        """Compare current results with the most recent previous run."""
        # Find previous reports
        reports = sorted(DATA_DIR.glob("benchmark_*.json"))
        if len(reports) < 1:
            return None

        # Load most recent previous
        try:
            with open(reports[-1], "r") as f:
                previous = json.load(f)
        except Exception:
            return None

        current = self.get_report()
        comparison = {"current_run": current["run_timestamp"], "changes": {}}

        for name in current["benchmarks"]:
            curr_pct = current["benchmarks"][name]["pct"]
            prev_pct = previous.get("benchmarks", {}).get(name, {}).get("pct", None)
            if prev_pct is not None:
                delta = round(curr_pct - prev_pct, 2)
                comparison["changes"][name] = {
                    "previous": prev_pct,
                    "current": curr_pct,
                    "delta": delta,
                    "trend": "improved" if delta > 0 else "declined" if delta < 0 else "stable",
                }

        return comparison


# ============================================================================
# Pretty Printing
# ============================================================================

def format_report_text(report: Dict) -> str:
    """Format a benchmark report as human-readable text."""
    lines = []
    lines.append("=" * 70)
    lines.append("  BRUCE AI - BENCHMARK REPORT")
    lines.append(f"  Run: {report.get('run_timestamp', 'N/A')}")
    lines.append("=" * 70)
    lines.append("")

    summary = report.get("summary", {})
    overall = summary.get("overall", {})
    lines.append(f"  OVERALL COMPOSITE SCORE: {overall.get('composite_score', 0)}%")
    lines.append(f"  Benchmarks run: {overall.get('benchmarks_run', 0)}")
    lines.append(f"  Benchmarks skipped: {overall.get('benchmarks_skipped', 0)}")
    lines.append("")
    lines.append("-" * 70)

    # Results table
    lines.append(f"  {'Benchmark':<25} {'Score':>10} {'Duration':>12}")
    lines.append(f"  {'-'*25} {'-'*10} {'-'*12}")

    for name, info in summary.items():
        if name == "overall":
            continue
        score_str = info.get("score", "N/A")
        dur_str = info.get("duration", "N/A")
        lines.append(f"  {name:<25} {score_str:>10} {dur_str:>12}")

    lines.append("-" * 70)
    lines.append("")

    # Detailed results per benchmark
    for bname, bdata in report.get("benchmarks", {}).items():
        lines.append(f"  [{bname.upper()}]")
        lines.append(f"    Score: {bdata.get('score', 0)} / {bdata.get('max_score', 0)} ({bdata.get('pct', 0)}%)")
        lines.append(f"    Duration: {bdata.get('duration_seconds', 0):.1f}s")

        meta = bdata.get("meta", {})
        if meta.get("skipped"):
            lines.append(f"    SKIPPED: {meta.get('reason', 'unknown')}")
        elif meta:
            for k, v in meta.items():
                if k == "skipped":
                    continue
                if isinstance(v, dict):
                    lines.append(f"    {k}:")
                    for mk, mv in v.items():
                        lines.append(f"      {mk}: {mv}")
                else:
                    lines.append(f"    {k}: {v}")
        lines.append("")

    lines.append("=" * 70)
    lines.append("  End of Report")
    lines.append("=" * 70)
    return "\n".join(lines)


def print_report(report: Dict) -> None:
    """Print the report to stdout."""
    print(format_report_text(report))


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Bruce AI Benchmark Suite")
    parser.add_argument("--name", type=str, default=None,
                        help="Run a specific benchmark (knowledge, quality, trading, hallucination, latency, memory)")
    parser.add_argument("--list", action="store_true", help="List available benchmarks")
    parser.add_argument("--quick", action="store_true", help="Run quick benchmark (subset)")
    parser.add_argument("--llm-eval", action="store_true", help="Use LLM for answer evaluation (slower, more accurate)")
    parser.add_argument("--provider", type=str, default="local", help="LLM provider (local, openai, anthropic, deepseek)")
    parser.add_argument("--no-save", action="store_true", help="Don't save results to disk")
    parser.add_argument("--compare", action="store_true", help="Compare with previous run")
    parser.add_argument("--trades-file", type=str, default=None, help="Path to paper trades JSON file")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

    if args.list:
        print("\nAvailable benchmarks:")
        print("-" * 40)
        for name in BenchmarkSuite.BENCHMARKS:
            print(f"  - {name}")
        print()
        return

    # Initialize LLM
    llm = None
    if LLM_AVAILABLE:
        try:
            llm = LLMBridge(provider=args.provider)
            print(f"[*] LLM initialized: {args.provider}")
        except Exception as e:
            print(f"[!] Could not initialize LLM ({args.provider}): {e}")
            print("[*] Benchmarks requiring LLM will be skipped.")

    suite = BenchmarkSuite(llm=llm, auto_init_llm=False)

    if args.quick:
        print("\n[*] Running quick benchmark...\n")
        suite.run_quick()
    elif args.name:
        print(f"\n[*] Running benchmark: {args.name}\n")
        try:
            suite.run_benchmark(args.name, use_llm_eval=args.llm_eval, trades_file=args.trades_file)
        except ValueError as e:
            print(f"[!] Error: {e}")
            return
    else:
        print("\n[*] Running all benchmarks...\n")
        suite.run_all(use_llm_eval=args.llm_eval)

    # Report
    report = suite.get_report()
    print_report(report)

    # Save
    if not args.no_save:
        json_path, txt_path = suite.save_report(report)
        print(f"\n[*] Results saved:")
        print(f"    JSON: {json_path}")
        print(f"    Text: {txt_path}")

    # Compare
    if args.compare:
        comparison = suite.compare_with_previous()
        if comparison:
            print("\n[*] Comparison with previous run:")
            print("-" * 50)
            for name, change in comparison.get("changes", {}).items():
                trend = change["trend"]
                delta = change["delta"]
                symbol = "+" if delta > 0 else "" if delta < 0 else " "
                print(f"  {name:<25} {symbol}{delta:>6.2f}%  ({trend})")
            print()
        else:
            print("\n[*] No previous run found for comparison.")


if __name__ == "__main__":
    main()
