"""
Bruce AI -- Internet Brain Module

Autonomous internet feeding and operating system. Bruce ALWAYS consumes
internet data when connected, learns from it, and acts on it.

Components:
    AutoFeed          - Continuous background data consumption (RSS, prices, on-chain, social, macro)
    InternetWorker    - Bruce performs research and monitoring tasks on the internet
    SmartDigest       - Generates intelligence reports from consumed data
    ConnectionManager - Detects and handles internet connectivity state
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger("Bruce.InternetBrain")

# ---------------------------------------------------------------------------
# Base directory for data persistence
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED_DATA_DIR = os.path.join(BASE_DIR, "data", "internet_brain")
INGESTED_LOG = os.path.join(FEED_DATA_DIR, "ingested_urls.json")
PRICE_HISTORY_FILE = os.path.join(FEED_DATA_DIR, "price_history.json")
ALERTS_FILE = os.path.join(FEED_DATA_DIR, "alerts.json")
DIGEST_DIR = os.path.join(FEED_DATA_DIR, "digests")

os.makedirs(FEED_DATA_DIR, exist_ok=True)
os.makedirs(DIGEST_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Rate-limit / good-citizen defaults
# ---------------------------------------------------------------------------
DEFAULT_REQUEST_DELAY = 2.0       # seconds between requests to the same domain
RSS_INTERVAL = 900                # 15 minutes
PRICE_INTERVAL = 300              # 5 minutes
ONCHAIN_INTERVAL = 600            # 10 minutes
SOCIAL_INTERVAL = 1800            # 30 minutes
MACRO_INTERVAL = 3600             # 1 hour
CONNECTIVITY_CHECK_INTERVAL = 30  # 30 seconds

USER_AGENT = "BruceAI/4.0 (+https://github.com/bruce-ai; autonomous-agent)"


# ============================================================
#  AutoFeed - Continuous Internet Data Consumption
# ============================================================

class AutoFeed:
    """Bruce continuously consumes internet data in the background."""

    FEED_SOURCES: Dict[str, List[str]] = {
        "crypto_news": [
            "https://coindesk.com/arc/outboundfeeds/rss/",
            "https://cointelegraph.com/rss",
            "https://decrypt.co/feed",
        ],
        "shipping_news": [
            "https://gcaptain.com/feed/",
            "https://splash247.com/feed/",
        ],
        "market_news": [
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        ],
        "macro_news": [
            "https://www.federalreserve.gov/feeds/press_all.xml",
            "https://feeds.reuters.com/reuters/businessNews",
        ],
        "tech_news": [
            "https://hnrss.org/frontpage",
            "https://www.reddit.com/r/artificial/.rss",
        ],
    }

    def __init__(self):
        self.is_running = False
        self._ingested_urls: Set[str] = set()
        self._price_history: List[Dict] = []
        self._alerts: List[Dict] = []
        self._knowledge_ingestor = None
        self._rag_engine = None
        self._last_domain_request: Dict[str, float] = {}
        self._load_ingested_urls()

    # ----- lazy loaders for shared modules --------------------------------

    def _get_ingestor(self):
        if self._knowledge_ingestor is None:
            try:
                from knowledge_ingestor import KnowledgeIngestor
                self._knowledge_ingestor = KnowledgeIngestor()
            except Exception as e:
                logger.warning("KnowledgeIngestor not available: %s", e)
        return self._knowledge_ingestor

    def _get_rag(self):
        if self._rag_engine is None:
            try:
                from modules.rag_engine import get_rag_engine
                self._rag_engine = get_rag_engine()
            except Exception as e:
                logger.debug("RAGEngine not available: %s", e)
        return self._rag_engine

    # ----- persistence ----------------------------------------------------

    def _load_ingested_urls(self):
        try:
            if os.path.exists(INGESTED_LOG):
                with open(INGESTED_LOG, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._ingested_urls = set(data.get("urls", []))
                    logger.debug("Loaded %d ingested URLs from disk", len(self._ingested_urls))
        except Exception as e:
            logger.warning("Could not load ingested URLs: %s", e)

    def _save_ingested_urls(self):
        try:
            # Keep only the last 10000 to avoid unbounded growth
            urls_list = list(self._ingested_urls)
            if len(urls_list) > 10000:
                urls_list = urls_list[-10000:]
                self._ingested_urls = set(urls_list)
            with open(INGESTED_LOG, "w", encoding="utf-8") as f:
                json.dump({"urls": urls_list, "updated": datetime.now(timezone.utc).isoformat()}, f)
        except Exception as e:
            logger.warning("Could not save ingested URLs: %s", e)

    def _already_ingested(self, url: str) -> bool:
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return url_hash in self._ingested_urls

    def _mark_ingested(self, url: str):
        url_hash = hashlib.md5(url.encode()).hexdigest()
        self._ingested_urls.add(url_hash)

    def _save_price_history(self):
        try:
            # Keep last 2000 entries
            history = self._price_history[-2000:]
            with open(PRICE_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f)
        except Exception as e:
            logger.warning("Could not save price history: %s", e)

    def _save_alert(self, alert: Dict):
        self._alerts.append(alert)
        try:
            existing = []
            if os.path.exists(ALERTS_FILE):
                with open(ALERTS_FILE, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            existing.append(alert)
            # Keep last 500 alerts
            existing = existing[-500:]
            with open(ALERTS_FILE, "w", encoding="utf-8") as f:
                json.dump(existing, f)
        except Exception as e:
            logger.warning("Could not save alert: %s", e)

    # ----- rate limiting --------------------------------------------------

    async def _rate_limit(self, domain: str):
        """Respect rate limits per domain."""
        now = time.time()
        last = self._last_domain_request.get(domain, 0)
        elapsed = now - last
        if elapsed < DEFAULT_REQUEST_DELAY:
            await asyncio.sleep(DEFAULT_REQUEST_DELAY - elapsed)
        self._last_domain_request[domain] = time.time()

    # ----- main entry point -----------------------------------------------

    async def start(self):
        """Start all background feed loops."""
        if self.is_running:
            logger.warning("AutoFeed is already running")
            return
        self.is_running = True
        logger.info("AutoFeed started -- consuming internet data in background")
        await asyncio.gather(
            self._feed_loop_rss(),
            self._feed_loop_prices(),
            self._feed_loop_onchain(),
            self._feed_loop_social(),
            self._feed_loop_macro(),
            return_exceptions=True,
        )

    async def stop(self):
        """Stop all feed loops."""
        self.is_running = False
        self._save_ingested_urls()
        logger.info("AutoFeed stopped")

    # ----- RSS feed loop --------------------------------------------------

    async def _feed_loop_rss(self):
        """Fetch RSS feeds, ingest new articles into knowledge base."""
        while self.is_running:
            try:
                total_new = 0
                for category, feeds in self.FEED_SOURCES.items():
                    for feed_url in feeds:
                        try:
                            articles = await self._parse_rss_async(feed_url)
                            for article in articles:
                                url = article.get("url", "")
                                if url and not self._already_ingested(url):
                                    text = article.get("title", "") + "\n" + article.get("summary", "")
                                    if text.strip():
                                        ingestor = self._get_ingestor()
                                        if ingestor:
                                            ingestor.ingest_text(
                                                text,
                                                source=url,
                                                metadata={
                                                    "domain": category,
                                                    "date": article.get("published", ""),
                                                    "title": article.get("title", ""),
                                                    "feed_source": feed_url,
                                                },
                                            )
                                        # Also index in RAG
                                        rag = self._get_rag()
                                        if rag:
                                            rag.index_document(
                                                text,
                                                metadata={
                                                    "source": url,
                                                    "domain": category,
                                                    "date": article.get("published", ""),
                                                },
                                            )
                                        self._mark_ingested(url)
                                        total_new += 1
                        except Exception as e:
                            logger.debug("RSS feed error for %s: %s", feed_url, e)
                        await asyncio.sleep(1)  # small delay between feeds
                if total_new > 0:
                    logger.info("AutoFeed RSS: ingested %d new articles", total_new)
                    self._save_ingested_urls()
            except Exception as e:
                logger.error("RSS feed loop error: %s", e)
            await asyncio.sleep(RSS_INTERVAL)

    async def _parse_rss_async(self, url: str) -> List[Dict]:
        """Parse RSS feed in executor to avoid blocking."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._parse_rss_sync, url)

    @staticmethod
    def _parse_rss_sync(url: str) -> List[Dict]:
        """Synchronous RSS parsing using the existing news_monitor module."""
        try:
            from modules.news_monitor import parse_rss
            return parse_rss(url)
        except Exception as e:
            logger.debug("RSS parse failed for %s: %s", url, e)
            return []

    # ----- Price feed loop ------------------------------------------------

    async def _feed_loop_prices(self):
        """Track prices and detect significant moves."""
        while self.is_running:
            try:
                prices = await self._fetch_prices_async()
                if prices:
                    entry = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "prices": prices,
                    }
                    self._price_history.append(entry)

                    # Detect significant moves (>3% in the last reading)
                    for coin_id, data in prices.items():
                        change = data.get("usd_24h_change", 0) or 0
                        if abs(change) > 3:
                            alert = {
                                "type": "price_alert",
                                "coin": coin_id,
                                "price": data.get("usd", 0),
                                "change_24h": round(change, 2),
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "message": f"{coin_id.upper()}: ${data.get('usd', 0):,.2f} ({change:+.1f}% 24h)",
                            }
                            self._save_alert(alert)
                            logger.info("PRICE ALERT: %s", alert["message"])

                    # Periodically save history
                    if len(self._price_history) % 12 == 0:  # every ~hour
                        self._save_price_history()
            except Exception as e:
                logger.debug("Price feed error: %s", e)
            await asyncio.sleep(PRICE_INTERVAL)

    async def _fetch_prices_async(self) -> Dict:
        """Fetch crypto prices from CoinGecko."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._fetch_prices_sync)

    @staticmethod
    def _fetch_prices_sync() -> Dict:
        try:
            import requests
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": "bitcoin,ethereum,solana",
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            }
            resp = requests.get(url, params=params, timeout=10,
                                headers={"User-Agent": USER_AGENT})
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.debug("CoinGecko price fetch failed: %s", e)
        return {}

    # ----- On-chain feed loop ---------------------------------------------

    async def _feed_loop_onchain(self):
        """Monitor on-chain data for whale movements, exchange flows."""
        while self.is_running:
            try:
                data = await self._fetch_onchain_async()
                if data:
                    # Ingest on-chain data as knowledge
                    summary = json.dumps(data, indent=2)
                    ingestor = self._get_ingestor()
                    if ingestor:
                        ingestor.ingest_text(
                            f"On-chain data snapshot:\n{summary}",
                            source="onchain_monitor",
                            metadata={"domain": "onchain", "type": "snapshot"},
                        )

                    # Alert on high fees or mempool congestion
                    fees = data.get("fees", {})
                    fastest = fees.get("fastestFee", 0)
                    if fastest > 100:  # sat/vB
                        alert = {
                            "type": "onchain_alert",
                            "message": f"BTC fees high: {fastest} sat/vB",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                        self._save_alert(alert)
            except Exception as e:
                logger.debug("On-chain feed error: %s", e)
            await asyncio.sleep(ONCHAIN_INTERVAL)

    async def _fetch_onchain_async(self) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._fetch_onchain_sync)

    @staticmethod
    def _fetch_onchain_sync() -> Dict:
        result = {}
        try:
            import requests
            # BTC fees from mempool.space
            resp = requests.get(
                "https://mempool.space/api/v1/fees/recommended",
                timeout=10, headers={"User-Agent": USER_AGENT},
            )
            if resp.status_code == 200:
                result["fees"] = resp.json()

            # BTC mempool stats
            resp2 = requests.get(
                "https://mempool.space/api/mempool",
                timeout=10, headers={"User-Agent": USER_AGENT},
            )
            if resp2.status_code == 200:
                result["mempool"] = resp2.json()
        except Exception as e:
            logger.debug("On-chain fetch error: %s", e)
        return result

    # ----- Social feed loop -----------------------------------------------

    async def _feed_loop_social(self):
        """Monitor Reddit/HN for trending topics and sentiment."""
        while self.is_running:
            try:
                # Hacker News top stories
                hn_data = await self._fetch_hn_async()
                if hn_data:
                    ingestor = self._get_ingestor()
                    for story in hn_data[:10]:
                        title = story.get("title", "")
                        url = story.get("url", "")
                        if title and url and not self._already_ingested(url):
                            if ingestor:
                                ingestor.ingest_text(
                                    title,
                                    source=url,
                                    metadata={"domain": "tech_social", "platform": "hackernews"},
                                )
                            self._mark_ingested(url)

                self._save_ingested_urls()
            except Exception as e:
                logger.debug("Social feed error: %s", e)
            await asyncio.sleep(SOCIAL_INTERVAL)

    async def _fetch_hn_async(self) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._fetch_hn_sync)

    @staticmethod
    def _fetch_hn_sync() -> List[Dict]:
        try:
            import requests
            resp = requests.get(
                "https://hacker-news.firebaseio.com/v0/topstories.json",
                timeout=10, headers={"User-Agent": USER_AGENT},
            )
            if resp.status_code != 200:
                return []
            story_ids = resp.json()[:15]
            stories = []
            for sid in story_ids:
                try:
                    sr = requests.get(
                        f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                        timeout=5, headers={"User-Agent": USER_AGENT},
                    )
                    if sr.status_code == 200:
                        stories.append(sr.json())
                except Exception:
                    continue
            return stories
        except Exception as e:
            logger.debug("HN fetch error: %s", e)
            return []

    # ----- Macro feed loop ------------------------------------------------

    async def _feed_loop_macro(self):
        """Monitor macro indicators -- Fear/Greed, yields, etc."""
        while self.is_running:
            try:
                macro = await self._fetch_macro_async()
                if macro:
                    summary = json.dumps(macro, indent=2)
                    ingestor = self._get_ingestor()
                    if ingestor:
                        ingestor.ingest_text(
                            f"Macro data snapshot:\n{summary}",
                            source="macro_monitor",
                            metadata={"domain": "macro", "type": "snapshot"},
                        )

                    # Alert on extreme fear/greed
                    fg = macro.get("fear_greed", {})
                    value = fg.get("value", 50)
                    if isinstance(value, (int, float)):
                        if value < 20:
                            self._save_alert({
                                "type": "macro_alert",
                                "message": f"Extreme Fear: Fear & Greed Index = {value}",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            })
                        elif value > 80:
                            self._save_alert({
                                "type": "macro_alert",
                                "message": f"Extreme Greed: Fear & Greed Index = {value}",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            })
            except Exception as e:
                logger.debug("Macro feed error: %s", e)
            await asyncio.sleep(MACRO_INTERVAL)

    async def _fetch_macro_async(self) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._fetch_macro_sync)

    @staticmethod
    def _fetch_macro_sync() -> Dict:
        result = {}
        try:
            import requests
            # Fear & Greed Index
            resp = requests.get(
                "https://api.alternative.me/fng/?limit=1",
                timeout=10, headers={"User-Agent": USER_AGENT},
            )
            if resp.status_code == 200:
                data = resp.json().get("data", [{}])[0]
                result["fear_greed"] = {
                    "value": int(data.get("value", 50)),
                    "classification": data.get("value_classification", "Neutral"),
                }
        except Exception as e:
            logger.debug("Macro fetch error: %s", e)
        return result

    # ----- public accessors -----------------------------------------------

    def get_recent_alerts(self, limit: int = 20) -> List[Dict]:
        """Get recent alerts."""
        return self._alerts[-limit:]

    def get_price_history(self, limit: int = 50) -> List[Dict]:
        """Get recent price history entries."""
        return self._price_history[-limit:]

    def get_feed_stats(self) -> Dict:
        """Get stats about the feed system."""
        return {
            "is_running": self.is_running,
            "urls_ingested": len(self._ingested_urls),
            "price_history_entries": len(self._price_history),
            "pending_alerts": len(self._alerts),
            "feed_categories": list(self.FEED_SOURCES.keys()),
            "feed_count": sum(len(v) for v in self.FEED_SOURCES.values()),
        }


# ============================================================
#  InternetWorker - Bruce Acts on the Internet
# ============================================================

class InternetWorker:
    """Bruce can perform research and monitoring tasks on the internet."""

    def __init__(self):
        self._monitored_topics: Dict[str, Dict] = {}
        self._tracked_entities: Dict[str, Dict] = {}

    def research(self, topic: str, max_pages: int = 5) -> Dict:
        """Deep research on any topic:
        1. Search DuckDuckGo for the topic
        2. Fetch top results
        3. Extract text from each
        4. Summarize findings
        5. Store in knowledge base
        Returns: {summary, sources, facts_learned, chunks_stored}
        """
        logger.info("Researching topic: %s", topic)
        try:
            from modules.web_browser import search_web, fetch_url
            from knowledge_ingestor import KnowledgeIngestor

            # Step 1: Search
            search_result = search_web(topic, max_results=max_pages)
            if not search_result.get("success"):
                return {"error": search_result.get("error", "Search failed"), "topic": topic}

            results = search_result.get("results", [])
            sources = []
            all_text = []
            total_chunks = 0

            ki = KnowledgeIngestor()

            # Step 2-4: Fetch and ingest each result
            for r in results[:max_pages]:
                url = r.get("url", "")
                if not url:
                    continue
                try:
                    page = fetch_url(url)
                    if page.get("success"):
                        text = page.get("text", "")
                        title = page.get("title", "")
                        if text:
                            result = ki.ingest_text(
                                text,
                                source=url,
                                metadata={
                                    "domain": "research",
                                    "topic": topic,
                                    "title": title,
                                },
                            )
                            total_chunks += result.get("chunks_added", 0)
                            all_text.append(f"[{title}]\n{text[:500]}")
                            sources.append({"title": title, "url": url})

                            # Also index in RAG
                            try:
                                from modules.rag_engine import get_rag_engine
                                rag = get_rag_engine()
                                rag.index_document(text, metadata={
                                    "source": url, "domain": "research", "topic": topic,
                                })
                            except Exception:
                                pass
                except Exception as e:
                    logger.debug("Could not fetch %s: %s", url, e)
                    continue
                time.sleep(DEFAULT_REQUEST_DELAY)  # rate limit

            # Step 5: Build summary
            combined = "\n\n---\n\n".join(all_text)
            summary = self._generate_summary(topic, combined)

            return {
                "topic": topic,
                "pages_researched": len(sources),
                "sources": sources,
                "chunks_stored": total_chunks,
                "summary": summary,
            }
        except Exception as e:
            logger.error("Research error for '%s': %s", topic, e)
            return {"error": str(e), "topic": topic}

    def monitor_topic(self, topic: str, interval_minutes: int = 60) -> Dict:
        """Set up continuous monitoring for a topic."""
        self._monitored_topics[topic] = {
            "topic": topic,
            "interval_minutes": interval_minutes,
            "created": datetime.now(timezone.utc).isoformat(),
            "last_checked": None,
            "alerts_sent": 0,
        }
        logger.info("Monitoring topic: %s (every %d min)", topic, interval_minutes)
        return {
            "status": "monitoring",
            "topic": topic,
            "interval_minutes": interval_minutes,
        }

    def track_entity(self, entity: str, entity_type: str = "crypto") -> Dict:
        """Track a specific entity (coin, company, ship, person)."""
        self._tracked_entities[entity] = {
            "entity": entity,
            "type": entity_type,
            "created": datetime.now(timezone.utc).isoformat(),
            "last_update": None,
        }

        # Do initial data fetch based on type
        if entity_type == "crypto":
            return self._track_crypto(entity)
        elif entity_type == "company":
            return self._track_company(entity)
        elif entity_type == "shipping":
            return self._track_shipping(entity)
        else:
            return self.research(entity)

    def competitive_intel(self, company: str) -> Dict:
        """Gather competitive intelligence on a company."""
        logger.info("Gathering competitive intel on: %s", company)
        results = {
            "company": company,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Search recent news
        try:
            from modules.web_browser import search_web
            news = search_web(f"{company} news latest", max_results=5)
            results["news"] = news.get("results", [])
        except Exception as e:
            results["news_error"] = str(e)

        # Check SEC filings
        try:
            from modules.edgar_sec import search_filings
            filings = search_filings(company)
            results["sec_filings"] = filings
        except Exception as e:
            results["sec_error"] = str(e)

        # Check stock price
        try:
            from modules.yahoo_finance import get_stock_price
            stock = get_stock_price(company)
            results["stock"] = stock
        except Exception as e:
            results["stock_error"] = str(e)

        return results

    def _track_crypto(self, coin: str) -> Dict:
        """Track a crypto entity."""
        result = {"entity": coin, "type": "crypto"}
        try:
            from modules.coingecko import get_price
            result["price_data"] = get_price(coin)
        except Exception as e:
            result["price_error"] = str(e)

        # Also research it
        research = self.research(f"{coin} cryptocurrency latest news analysis")
        result["research"] = research
        return result

    def _track_company(self, company: str) -> Dict:
        """Track a company entity."""
        return self.competitive_intel(company)

    def _track_shipping(self, entity: str) -> Dict:
        """Track a shipping entity."""
        result = {"entity": entity, "type": "shipping"}
        try:
            from modules.news_monitor import get_shipping_news
            news = get_shipping_news()
            # Filter for relevant articles
            articles = news.get("articles", [])
            relevant = [a for a in articles if entity.lower() in a.get("title", "").lower()]
            result["relevant_news"] = relevant[:10]
            result["total_shipping_news"] = len(articles)
        except Exception as e:
            result["error"] = str(e)
        return result

    def get_monitored_topics(self) -> List[Dict]:
        """Get all monitored topics."""
        return list(self._monitored_topics.values())

    def get_tracked_entities(self) -> List[Dict]:
        """Get all tracked entities."""
        return list(self._tracked_entities.values())

    @staticmethod
    def _generate_summary(topic: str, text: str) -> str:
        """Generate a summary using the LLM if available, else extract key sentences."""
        # Try LLM
        try:
            from llm_client import get_llm
            client = get_llm()
            if client.is_available():
                prompt = (
                    f"Summarize the following research on '{topic}' in 3-5 bullet points. "
                    f"Focus on key facts, numbers, and actionable insights:\n\n{text[:3000]}"
                )
                return client.generate(prompt)
        except Exception:
            pass

        # Fallback: extract first sentences from each section
        sections = text.split("---")
        summary_parts = []
        for section in sections[:5]:
            lines = section.strip().split("\n")
            if lines:
                summary_parts.append(lines[0][:200])
        return "Key findings:\n" + "\n".join(f"- {p}" for p in summary_parts)


# ============================================================
#  SmartDigest - Intelligence Reports
# ============================================================

class SmartDigest:
    """Bruce generates periodic intelligence digests from consumed data."""

    def __init__(self, auto_feed: Optional[AutoFeed] = None):
        self._auto_feed = auto_feed

    def generate_morning_brief(self) -> str:
        """Generate a morning intelligence brief covering overnight activity."""
        logger.info("Generating morning brief")
        sections = []
        sections.append(f"=== BRUCE AI MORNING BRIEF ===")
        sections.append(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        sections.append("")

        # 1. Crypto prices
        try:
            import requests
            resp = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": "bitcoin,ethereum,solana",
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                },
                timeout=10, headers={"User-Agent": USER_AGENT},
            )
            if resp.status_code == 200:
                data = resp.json()
                sections.append("--- CRYPTO PRICES ---")
                for coin, info in data.items():
                    price = info.get("usd", 0)
                    change = info.get("usd_24h_change", 0) or 0
                    arrow = "+" if change > 0 else ""
                    sections.append(f"  {coin.upper()}: ${price:,.2f} ({arrow}{change:.1f}%)")
                sections.append("")
        except Exception as e:
            sections.append(f"  [Prices unavailable: {e}]")

        # 2. Fear & Greed
        try:
            import requests
            resp = requests.get(
                "https://api.alternative.me/fng/?limit=1",
                timeout=10, headers={"User-Agent": USER_AGENT},
            )
            if resp.status_code == 200:
                fg = resp.json().get("data", [{}])[0]
                sections.append(f"--- SENTIMENT ---")
                sections.append(f"  Fear & Greed: {fg.get('value', '?')} ({fg.get('value_classification', '?')})")
                sections.append("")
        except Exception:
            pass

        # 3. Top news headlines
        try:
            from modules.news_monitor import get_crypto_news, get_market_news, get_sentiment
            crypto_news = get_crypto_news(max_total=5)
            market_news = get_market_news(max_total=5)

            if crypto_news.get("articles"):
                headlines = [a["title"] for a in crypto_news["articles"]]
                sentiment = get_sentiment(headlines)
                sections.append(f"--- CRYPTO NEWS (sentiment: {sentiment['overall']}) ---")
                for a in crypto_news["articles"][:5]:
                    sections.append(f"  - [{a.get('source', '')}] {a['title']}")
                sections.append("")

            if market_news.get("articles"):
                headlines = [a["title"] for a in market_news["articles"]]
                sentiment = get_sentiment(headlines)
                sections.append(f"--- MARKET NEWS (sentiment: {sentiment['overall']}) ---")
                for a in market_news["articles"][:5]:
                    sections.append(f"  - [{a.get('source', '')}] {a['title']}")
                sections.append("")
        except Exception as e:
            sections.append(f"  [News unavailable: {e}]")

        # 4. Recent alerts
        if self._auto_feed:
            alerts = self._auto_feed.get_recent_alerts(10)
            if alerts:
                sections.append("--- RECENT ALERTS ---")
                for a in alerts[-5:]:
                    sections.append(f"  [{a.get('type', 'alert')}] {a.get('message', '')}")
                sections.append("")

        sections.append("=== END MORNING BRIEF ===")

        brief = "\n".join(sections)

        # Save to file
        try:
            filename = datetime.now().strftime("brief_%Y%m%d_%H%M.txt")
            filepath = os.path.join(DIGEST_DIR, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(brief)
        except Exception:
            pass

        return brief

    def generate_market_alert(self, event: Dict) -> str:
        """Generate alert for significant market event."""
        lines = [
            f"MARKET ALERT: {event.get('type', 'Unknown Event')}",
            f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            f"What happened: {event.get('description', 'N/A')}",
            f"Impact: {event.get('impact', 'Unknown')}",
        ]

        if event.get("price"):
            lines.append(f"Price: ${event['price']:,.2f}")
        if event.get("change"):
            lines.append(f"Change: {event['change']:+.2f}%")

        lines.append("")
        lines.append(f"Recommendation: {event.get('action', 'Monitor closely')}")

        return "\n".join(lines)

    def generate_weekly_report(self) -> str:
        """Weekly performance and market review."""
        logger.info("Generating weekly report")
        sections = []
        sections.append(f"=== BRUCE AI WEEKLY REPORT ===")
        sections.append(f"Week ending: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
        sections.append("")

        # Price history summary
        if self._auto_feed:
            history = self._auto_feed.get_price_history(288)  # ~1 week at 5 min intervals
            if history:
                sections.append("--- PRICE SUMMARY ---")
                first = history[0].get("prices", {})
                last = history[-1].get("prices", {})
                for coin in ["bitcoin", "ethereum", "solana"]:
                    start_price = first.get(coin, {}).get("usd", 0)
                    end_price = last.get(coin, {}).get("usd", 0)
                    if start_price and end_price:
                        change_pct = ((end_price - start_price) / start_price) * 100
                        sections.append(
                            f"  {coin.upper()}: ${start_price:,.2f} -> ${end_price:,.2f} ({change_pct:+.1f}%)"
                        )
                sections.append("")

            # Alert summary
            alerts = self._auto_feed.get_recent_alerts(100)
            if alerts:
                alert_types = {}
                for a in alerts:
                    t = a.get("type", "other")
                    alert_types[t] = alert_types.get(t, 0) + 1
                sections.append("--- ALERTS SUMMARY ---")
                for t, count in alert_types.items():
                    sections.append(f"  {t}: {count} alerts")
                sections.append("")

            # Feed stats
            stats = self._auto_feed.get_feed_stats()
            sections.append("--- FEED STATS ---")
            sections.append(f"  URLs ingested: {stats.get('urls_ingested', 0)}")
            sections.append(f"  Price history entries: {stats.get('price_history_entries', 0)}")
            sections.append("")

        sections.append("=== END WEEKLY REPORT ===")

        report = "\n".join(sections)

        # Save
        try:
            filename = datetime.now().strftime("weekly_%Y%m%d.txt")
            filepath = os.path.join(DIGEST_DIR, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report)
        except Exception:
            pass

        return report


# ============================================================
#  ConnectionManager - Detect and Handle Internet State
# ============================================================

class ConnectionManager:
    """Manages internet connectivity state for Bruce."""

    CONNECTIVITY_ENDPOINTS = [
        "https://api.coingecko.com/api/v3/ping",
        "https://httpbin.org/get",
        "https://dns.google/resolve?name=google.com",
    ]

    def __init__(self):
        self._connected = False
        self._last_check: Optional[str] = None
        self._on_connect_callbacks: List[Callable] = []
        self._on_disconnect_callbacks: List[Callable] = []
        self._queued_alerts: List[Dict] = []

    def is_connected(self) -> bool:
        """Quick check if internet is available."""
        try:
            import requests
            for endpoint in self.CONNECTIVITY_ENDPOINTS:
                try:
                    resp = requests.get(endpoint, timeout=5, headers={"User-Agent": USER_AGENT})
                    if resp.status_code == 200:
                        self._last_check = datetime.now(timezone.utc).isoformat()
                        return True
                except Exception:
                    continue
        except ImportError:
            pass
        return False

    def on_connect(self):
        """Called when internet becomes available."""
        logger.info("Internet CONNECTED -- syncing data and starting feeds")
        self._connected = True

        # Send any queued alerts
        if self._queued_alerts:
            logger.info("Sending %d queued alerts", len(self._queued_alerts))
            try:
                from modules.telegram_alerts import send_alert
                for alert in self._queued_alerts:
                    send_alert(alert.get("message", ""))
                self._queued_alerts.clear()
            except Exception as e:
                logger.warning("Could not send queued alerts: %s", e)

        # Call registered callbacks
        for cb in self._on_connect_callbacks:
            try:
                cb()
            except Exception as e:
                logger.warning("on_connect callback error: %s", e)

    def on_disconnect(self):
        """Called when internet is lost."""
        logger.warning("Internet DISCONNECTED -- switching to offline mode")
        self._connected = False

        for cb in self._on_disconnect_callbacks:
            try:
                cb()
            except Exception as e:
                logger.warning("on_disconnect callback error: %s", e)

    def queue_alert(self, message: str):
        """Queue an alert for when connectivity returns."""
        self._queued_alerts.append({
            "message": message,
            "queued_at": datetime.now(timezone.utc).isoformat(),
        })

    async def monitor_connection(self):
        """Background loop checking connectivity every 30 seconds."""
        while True:
            try:
                loop = asyncio.get_event_loop()
                connected = await loop.run_in_executor(None, self.is_connected)

                if connected and not self._connected:
                    self.on_connect()
                elif not connected and self._connected:
                    self.on_disconnect()

                self._connected = connected
            except Exception as e:
                logger.debug("Connection monitor error: %s", e)
            await asyncio.sleep(CONNECTIVITY_CHECK_INTERVAL)

    def register_on_connect(self, callback: Callable):
        """Register a callback for when internet becomes available."""
        self._on_connect_callbacks.append(callback)

    def register_on_disconnect(self, callback: Callable):
        """Register a callback for when internet is lost."""
        self._on_disconnect_callbacks.append(callback)

    def get_status(self) -> Dict:
        return {
            "connected": self._connected,
            "last_check": self._last_check,
            "queued_alerts": len(self._queued_alerts),
        }


# ============================================================
#  InternetBrain -- Unified Facade
# ============================================================

class InternetBrain:
    """Unified facade combining all internet brain components.

    Usage:
        brain = InternetBrain()
        await brain.start()    # starts all background feeds + connection monitor
        brain.research("topic")
        brain.morning_brief()
    """

    def __init__(self):
        self.auto_feed = AutoFeed()
        self.worker = InternetWorker()
        self.connection = ConnectionManager()
        self.digest = SmartDigest(auto_feed=self.auto_feed)

        # Wire up connection callbacks
        self.connection.register_on_connect(self._on_internet_available)
        self.connection.register_on_disconnect(self._on_internet_lost)

    def _on_internet_available(self):
        """Start feeds when internet comes online."""
        if not self.auto_feed.is_running:
            # Schedule feed start on the event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(self.auto_feed.start())
            except Exception as e:
                logger.debug("Could not auto-start feeds: %s", e)

    def _on_internet_lost(self):
        """Pause feeds when internet goes down."""
        if self.auto_feed.is_running:
            self.auto_feed.is_running = False
            logger.info("AutoFeed paused due to lost connectivity")

    async def start(self):
        """Start the internet brain -- feeds + connection monitor."""
        logger.info("InternetBrain starting...")

        # Check connectivity first
        connected = self.connection.is_connected()
        if connected:
            self.connection.on_connect()

        # Start background tasks
        await asyncio.gather(
            self.connection.monitor_connection(),
            self.auto_feed.start() if connected else asyncio.sleep(0),
            return_exceptions=True,
        )

    async def stop(self):
        """Stop the internet brain."""
        await self.auto_feed.stop()
        logger.info("InternetBrain stopped")

    # ----- convenience proxies --------------------------------------------

    def research(self, topic: str, max_pages: int = 5) -> Dict:
        return self.worker.research(topic, max_pages)

    def monitor_topic(self, topic: str, interval_minutes: int = 60) -> Dict:
        return self.worker.monitor_topic(topic, interval_minutes)

    def track_entity(self, entity: str, entity_type: str = "crypto") -> Dict:
        return self.worker.track_entity(entity, entity_type)

    def competitive_intel(self, company: str) -> Dict:
        return self.worker.competitive_intel(company)

    def morning_brief(self) -> str:
        return self.digest.generate_morning_brief()

    def weekly_report(self) -> str:
        return self.digest.generate_weekly_report()

    def market_alert(self, event: Dict) -> str:
        return self.digest.generate_market_alert(event)

    def get_status(self) -> Dict:
        return {
            "connection": self.connection.get_status(),
            "feed": self.auto_feed.get_feed_stats(),
            "monitored_topics": len(self.worker.get_monitored_topics()),
            "tracked_entities": len(self.worker.get_tracked_entities()),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_brain: Optional[InternetBrain] = None


def get_internet_brain() -> InternetBrain:
    """Get or create the singleton InternetBrain."""
    global _brain
    if _brain is None:
        _brain = InternetBrain()
    return _brain
