#!/usr/bin/env python3
"""
Bruce AI - Mega Knowledge Training Script
==========================================
Downloads FREE, publicly available knowledge from Wikipedia and Investopedia,
then ingests it into Bruce's KnowledgeIngestor and RAG engine (ChromaDB).

Usage:
    python scripts/mega_train.py              # Train all domains
    python scripts/mega_train.py --domain shipping   # Train one domain
    python scripts/mega_train.py --list        # List all available topics
    python scripts/mega_train.py --dry-run     # Show what would be fetched without ingesting

Sources are Wikipedia REST API (public domain) and Investopedia (public articles).
"""

import argparse
import json
import logging
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from knowledge_ingestor import KnowledgeIngestor

# Try to import RAG engine
try:
    from modules.rag_engine import RAGEngine

    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("MegaTrain")

# ---------------------------------------------------------------------------
# HTTP setup
# ---------------------------------------------------------------------------
try:
    import requests
    from bs4 import BeautifulSoup

    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False
    logger.error("Missing dependencies: pip install requests beautifulsoup4")
    sys.exit(1)

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "BruceAI-MegaTrain/1.0 (Knowledge Training Script; polite bot; +https://github.com/bruceai)",
        "Accept": "application/json",
    }
)

# Polite delay between requests (seconds)
REQUEST_DELAY = 0.5
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # exponential backoff multiplier

# ---------------------------------------------------------------------------
# Knowledge Sources
# ---------------------------------------------------------------------------

SOURCES: Dict[str, Dict[str, List[str]]] = {
    "shipping": {
        "wikipedia": [
            "Container_ship",
            "Bulk_carrier",
            "Tanker_(ship)",
            "LNG_carrier",
            "Incoterms",
            "Bill_of_lading",
            "Charter_party",
            "Panama_Canal",
            "Suez_Canal",
            "Strait_of_Malacca",
            "Strait_of_Hormuz",
            "Baltic_Exchange",
            "Freight_rate",
            "Twenty-foot_equivalent_unit",
            "International_Maritime_Organization",
            "SOLAS_Convention",
            "MARPOL",
            "Port_of_Shanghai",
            "Port_of_Rotterdam",
            "Port_of_Singapore",
            "Maritime_law",
            "Admiralty_law",
            "Cabotage",
            "Panamax",
            "Capesize",
            "Handysize",
            "Supramax",
        ],
        "investopedia": [
            "incoterms",
            "bill-of-lading",
            "free-on-board-fob",
            "cost-insurance-and-freight-cif",
            "freight-on-board-fob",
            "demurrage",
        ],
    },
    "crypto": {
        "wikipedia": [
            "Bitcoin",
            "Ethereum",
            "Solana_(blockchain_platform)",
            "Cryptocurrency",
            "Blockchain",
            "Smart_contract",
            "Decentralized_finance",
            "Decentralized_exchange",
            "Proof_of_work",
            "Proof_of_stake",
            "Bitcoin_halving",
            "Tokenomics",
            "Stablecoin",
            "Non-fungible_token",
            "Layer_2_(blockchain)",
            "Cryptocurrency_exchange",
            "Liquidity_pool",
            "Maximal_extractable_value",
            "Flash_loan",
            "Yield_farming",
        ],
        "investopedia": [
            "bitcoin",
            "ethereum",
            "blockchain",
            "smart-contracts",
            "decentralized-finance-defi",
            "stablecoin",
            "non-fungible-token-nft",
            "proof-of-work",
            "proof-of-stake-pos",
            "yield-farming",
            "liquidity-pool",
            "tokenomics",
        ],
    },
    "trading": {
        "wikipedia": [
            "Technical_analysis",
            "Fundamental_analysis",
            "Moving_average",
            "Relative_strength_index",
            "MACD",
            "Bollinger_Bands",
            "Option_(finance)",
            "Futures_contract",
            "Derivative_(finance)",
            "Hedge_fund",
            "Portfolio_theory",
            "Modern_portfolio_theory",
            "Black%E2%80%93Scholes_model",
            "Value_at_risk",
            "Algorithmic_trading",
            "High-frequency_trading",
            "Market_maker",
            "Order_book_(trading)",
            "Bid%E2%80%93ask_spread",
            "Bull_market",
            "Bear_market",
            "Market_correction",
            "Federal_Reserve",
            "Interest_rate",
            "Inflation",
            "Quantitative_easing",
            "Yield_curve",
        ],
        "investopedia": [
            "technicalanalysis",
            "fundamentalanalysis",
            "movingaverage",
            "rsi",
            "macd",
            "bollingerbands",
            "option",
            "futurescontract",
            "derivative",
            "hedgefund",
            "modernportfoliotheory-mpt",
            "blackscholes-model",
            "var",
            "algorithmictrading",
            "high-frequency-trading-hft",
            "marketmaker",
            "bid-and-ask",
            "bullmarket",
            "bearmarket",
        ],
    },
    "macro": {
        "wikipedia": [
            "Gross_domestic_product",
            "Balance_of_trade",
            "Foreign_exchange_market",
            "Currency_pair",
            "Commodity_market",
            "Gold_standard",
            "OPEC",
            "Petrodollar_recycling",
            "Price_of_oil",
            "U.S._Dollar_Index",
            "United_States_Treasury_security",
            "Geopolitics",
            "Trade_war",
            "Economic_sanctions",
            "Supply_chain",
            "Global_supply_chain_finance",
            "Economic_indicator",
            "Leading_indicator",
        ],
        "investopedia": [
            "gdp",
            "balance-of-trade",
            "forex",
            "commodity",
            "gold-standard",
            "opec",
            "petrodollars",
            "usdx",
            "geopolitics",
            "trade-war",
            "economic-indicator",
        ],
    },
    "ai_ml": {
        "wikipedia": [
            "Artificial_intelligence",
            "Machine_learning",
            "Neural_network_(machine_learning)",
            "Deep_learning",
            "Transformer_(deep_learning_architecture)",
            "Reinforcement_learning",
            "Proximal_policy_optimization",
            "Natural_language_processing",
            "Large_language_model",
            "Retrieval-augmented_generation",
            "Vector_database",
            "Word_embedding",
        ],
        "investopedia": [
            "artificial-intelligence-ai",
            "machine-learning",
            "deep-learning",
            "neural-network",
        ],
    },
    "risk": {
        "wikipedia": [
            "Risk_management",
            "Financial_risk",
            "Credit_risk",
            "Market_risk",
            "Operational_risk",
            "Stress_testing_(financial)",
            "Monte_Carlo_method",
            "Diversification_(finance)",
            "Hedge_(finance)",
            "Insurance",
        ],
        "investopedia": [
            "riskmanagement",
            "financialrisk",
            "creditrisk",
            "marketrisk",
            "operationalrisk",
            "stresstesting",
            "montecarlosimulation",
            "diversification",
            "hedge",
        ],
    },
}


# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------


def _request_with_retry(url: str, retries: int = MAX_RETRIES) -> Optional[requests.Response]:
    """Make an HTTP GET with exponential backoff retries."""
    for attempt in range(retries):
        try:
            resp = SESSION.get(url, timeout=20)
            if resp.status_code == 429:
                wait = RETRY_BACKOFF ** (attempt + 1)
                logger.warning("Rate limited (429). Waiting %.1fs before retry...", wait)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout:
            logger.warning("Timeout fetching %s (attempt %d/%d)", url, attempt + 1, retries)
            time.sleep(RETRY_BACKOFF ** attempt)
        except requests.exceptions.ConnectionError:
            logger.warning("Connection error for %s (attempt %d/%d)", url, attempt + 1, retries)
            time.sleep(RETRY_BACKOFF ** attempt)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.warning("Article not found (404): %s", url)
                return None
            logger.warning("HTTP error %s (attempt %d/%d): %s", url, attempt + 1, retries, e)
            time.sleep(RETRY_BACKOFF ** attempt)
        except Exception as e:
            logger.warning("Unexpected error fetching %s: %s", url, e)
            time.sleep(RETRY_BACKOFF ** attempt)
    logger.error("Failed to fetch %s after %d attempts", url, retries)
    return None


def fetch_wikipedia(title: str) -> Optional[Tuple[str, str]]:
    """
    Fetch a Wikipedia article's full plain-text extract via the MediaWiki API.
    Returns (display_title, full_text) or None on failure.
    """
    # Use the MediaWiki API for full article text (plaintext extracts)
    api_url = (
        "https://en.wikipedia.org/w/api.php?"
        "action=query"
        f"&titles={urllib.parse.quote(title, safe='')}"
        "&prop=extracts"
        "&exintro=0"
        "&explaintext=1"
        "&format=json"
        "&redirects=1"
    )

    resp = _request_with_retry(api_url)
    if resp is None:
        return None

    try:
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if page_id == "-1":
                logger.warning("Wikipedia article not found: %s", title)
                return None
            display_title = page_data.get("title", title)
            extract = page_data.get("extract", "")
            if not extract or len(extract.strip()) < 100:
                logger.warning("Wikipedia article too short or empty: %s", title)
                return None
            return (display_title, extract.strip())
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Failed to parse Wikipedia response for %s: %s", title, e)
    return None


def fetch_investopedia(slug: str) -> Optional[Tuple[str, str]]:
    """
    Fetch an Investopedia article by slug.
    Returns (title, text) or None on failure.
    """
    # Investopedia uses /terms/<first-letter>/<slug>.asp pattern
    # But also supports /terms/<slug> - try both
    urls_to_try = [
        f"https://www.investopedia.com/terms/{slug[0]}/{slug}.asp",
        f"https://www.investopedia.com/terms/{slug}.asp",
    ]

    for url in urls_to_try:
        resp = _request_with_retry(url)
        if resp is None:
            continue

        try:
            soup = BeautifulSoup(resp.text, "html.parser")

            # Remove noise elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "figure", "figcaption"]):
                tag.decompose()

            # Remove ad containers and related content
            for cls in ["ad-container", "related-terms", "sidebar", "cookie-banner"]:
                for el in soup.find_all(class_=re.compile(cls, re.I)):
                    el.decompose()

            # Get title
            title_tag = soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else slug.replace("-", " ").title()

            # Get main article content
            article = soup.find("article") or soup.find("div", class_=re.compile("article-body", re.I))
            if article:
                text = article.get_text(separator="\n", strip=True)
            else:
                # Fallback: get body text
                text = soup.get_text(separator="\n", strip=True)

            # Clean up
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = re.sub(r" {2,}", " ", text)

            if len(text.strip()) < 200:
                continue

            return (title, text.strip())

        except Exception as e:
            logger.warning("Failed to parse Investopedia page %s: %s", url, e)
            continue

    return None


# ---------------------------------------------------------------------------
# Training orchestrator
# ---------------------------------------------------------------------------


class MegaTrainer:
    """Orchestrates bulk knowledge ingestion across all sources and domains."""

    def __init__(self, domains: Optional[List[str]] = None):
        self.ki = KnowledgeIngestor()
        self.rag = None
        if RAG_AVAILABLE:
            try:
                self.rag = RAGEngine()
                logger.info("RAG engine (ChromaDB) initialized successfully")
            except Exception as e:
                logger.warning("RAG engine init failed (will continue without it): %s", e)

        self.target_domains = domains  # None means all
        self.stats = {
            "domains_trained": [],
            "total_articles_fetched": 0,
            "total_articles_failed": 0,
            "total_chunks_knowledge": 0,
            "total_chunks_rag": 0,
            "total_characters": 0,
            "per_domain": {},
            "failed_articles": [],
            "start_time": None,
            "end_time": None,
        }

    def _get_domains(self) -> List[str]:
        """Return list of domains to process."""
        if self.target_domains:
            valid = [d for d in self.target_domains if d in SOURCES]
            invalid = [d for d in self.target_domains if d not in SOURCES]
            if invalid:
                logger.warning("Unknown domains (skipping): %s", ", ".join(invalid))
            return valid
        return list(SOURCES.keys())

    def _ingest(self, text: str, source: str, domain: str, title: str) -> Tuple[int, int]:
        """Ingest text into both KnowledgeIngestor and RAG engine. Returns (ki_chunks, rag_chunks)."""
        metadata = {
            "domain": domain,
            "title": title,
            "trained_at": datetime.now(timezone.utc).isoformat(),
        }

        # KnowledgeIngestor
        ki_result = self.ki.ingest_text(
            text, source=source, metadata=metadata, chunk_size=500, overlap=50
        )
        ki_chunks = ki_result.get("chunks_added", 0)

        # RAG Engine
        rag_chunks = 0
        if self.rag is not None:
            try:
                rag_meta = dict(metadata)
                rag_meta["source"] = source
                rag_result = self.rag.index_document(text, metadata=rag_meta)
                rag_chunks = rag_result.get("chunks_indexed", 0)
            except Exception as e:
                logger.warning("RAG indexing failed for %s: %s", source, e)

        return ki_chunks, rag_chunks

    def train_domain(self, domain: str) -> Dict:
        """Train a single domain from all its sources."""
        domain_sources = SOURCES.get(domain)
        if not domain_sources:
            logger.error("Unknown domain: %s", domain)
            return {}

        domain_stats = {
            "articles_fetched": 0,
            "articles_failed": 0,
            "chunks_knowledge": 0,
            "chunks_rag": 0,
            "characters": 0,
            "sources": {"wikipedia": 0, "investopedia": 0},
        }

        total_articles = sum(len(v) for v in domain_sources.values())
        logger.info("=" * 60)
        logger.info("DOMAIN: %s (%d articles)", domain.upper(), total_articles)
        logger.info("=" * 60)

        # Wikipedia articles
        wiki_articles = domain_sources.get("wikipedia", [])
        for i, article_title in enumerate(wiki_articles, 1):
            display_name = article_title.replace("_", " ")
            logger.info(
                "  [%s] Wikipedia %d/%d: %s",
                domain, i, len(wiki_articles), display_name,
            )

            result = fetch_wikipedia(article_title)
            if result is None:
                domain_stats["articles_failed"] += 1
                self.stats["failed_articles"].append(f"wiki:{domain}/{article_title}")
                continue

            title, text = result
            source_key = f"wikipedia_{domain}_{article_title}"
            ki_chunks, rag_chunks = self._ingest(text, source_key, domain, title)

            domain_stats["articles_fetched"] += 1
            domain_stats["chunks_knowledge"] += ki_chunks
            domain_stats["chunks_rag"] += rag_chunks
            domain_stats["characters"] += len(text)
            domain_stats["sources"]["wikipedia"] += 1

            logger.info(
                "    -> %s: %d chars, %d KB chunks, %d RAG chunks",
                title, len(text), ki_chunks, rag_chunks,
            )

            time.sleep(REQUEST_DELAY)

        # Investopedia articles
        inv_articles = domain_sources.get("investopedia", [])
        for i, slug in enumerate(inv_articles, 1):
            display_name = slug.replace("-", " ").title()
            logger.info(
                "  [%s] Investopedia %d/%d: %s",
                domain, i, len(inv_articles), display_name,
            )

            result = fetch_investopedia(slug)
            if result is None:
                domain_stats["articles_failed"] += 1
                self.stats["failed_articles"].append(f"investopedia:{domain}/{slug}")
                logger.warning("    -> FAILED to fetch")
                continue

            title, text = result
            source_key = f"investopedia_{domain}_{slug}"
            ki_chunks, rag_chunks = self._ingest(text, source_key, domain, title)

            domain_stats["articles_fetched"] += 1
            domain_stats["chunks_knowledge"] += ki_chunks
            domain_stats["chunks_rag"] += rag_chunks
            domain_stats["characters"] += len(text)
            domain_stats["sources"]["investopedia"] += 1

            logger.info(
                "    -> %s: %d chars, %d KB chunks, %d RAG chunks",
                title, len(text), ki_chunks, rag_chunks,
            )

            time.sleep(REQUEST_DELAY)

        # Domain summary
        logger.info("-" * 40)
        logger.info(
            "  %s complete: %d fetched, %d failed, %d KB chunks, %d RAG chunks, %d chars",
            domain.upper(),
            domain_stats["articles_fetched"],
            domain_stats["articles_failed"],
            domain_stats["chunks_knowledge"],
            domain_stats["chunks_rag"],
            domain_stats["characters"],
        )
        logger.info("")

        return domain_stats

    def train_all(self):
        """Train all selected domains."""
        self.stats["start_time"] = datetime.now(timezone.utc).isoformat()
        domains = self._get_domains()

        if not domains:
            logger.error("No valid domains to train!")
            return

        total_articles = sum(
            sum(len(v) for v in SOURCES[d].values())
            for d in domains
        )

        logger.info("*" * 60)
        logger.info("BRUCE AI - MEGA KNOWLEDGE TRAINING")
        logger.info("*" * 60)
        logger.info("Domains: %s", ", ".join(domains))
        logger.info("Total articles to fetch: %d", total_articles)
        logger.info("RAG engine: %s", "ENABLED" if self.rag else "DISABLED")
        logger.info("*" * 60)
        logger.info("")

        for domain in domains:
            domain_stats = self.train_domain(domain)
            if domain_stats:
                self.stats["domains_trained"].append(domain)
                self.stats["per_domain"][domain] = domain_stats
                self.stats["total_articles_fetched"] += domain_stats["articles_fetched"]
                self.stats["total_articles_failed"] += domain_stats["articles_failed"]
                self.stats["total_chunks_knowledge"] += domain_stats["chunks_knowledge"]
                self.stats["total_chunks_rag"] += domain_stats["chunks_rag"]
                self.stats["total_characters"] += domain_stats["characters"]

        self.stats["end_time"] = datetime.now(timezone.utc).isoformat()

        self._print_final_report()
        self._save_training_summary()

    def _print_final_report(self):
        """Print final training stats."""
        logger.info("")
        logger.info("*" * 60)
        logger.info("TRAINING COMPLETE")
        logger.info("*" * 60)
        logger.info("")
        logger.info("  Domains trained:        %d  (%s)", len(self.stats["domains_trained"]), ", ".join(self.stats["domains_trained"]))
        logger.info("  Articles fetched:       %d", self.stats["total_articles_fetched"])
        logger.info("  Articles failed:        %d", self.stats["total_articles_failed"])
        logger.info("  Knowledge chunks:       %d", self.stats["total_chunks_knowledge"])
        logger.info("  RAG chunks indexed:     %d", self.stats["total_chunks_rag"])
        logger.info("  Total characters:       %s", f"{self.stats['total_characters']:,}")
        logger.info("")

        if self.stats["per_domain"]:
            logger.info("  Per-domain breakdown:")
            for domain, ds in self.stats["per_domain"].items():
                logger.info(
                    "    %-12s  %3d articles | %4d KB chunks | %4d RAG chunks | %s chars",
                    domain,
                    ds["articles_fetched"],
                    ds["chunks_knowledge"],
                    ds["chunks_rag"],
                    f"{ds['characters']:,}",
                )

        if self.stats["failed_articles"]:
            logger.info("")
            logger.info("  Failed articles (%d):", len(self.stats["failed_articles"]))
            for fa in self.stats["failed_articles"]:
                logger.info("    - %s", fa)

        # Knowledge base stats
        kb_stats = self.ki.get_knowledge_stats()
        logger.info("")
        logger.info("  Knowledge base totals:")
        logger.info("    Total chunks on disk:   %d", kb_stats.get("total_chunks", 0))
        logger.info("    Total sources:          %d", kb_stats.get("total_sources", 0))
        logger.info("    Disk size:              %s KB", f"{kb_stats.get('disk_size_bytes', 0) / 1024:.1f}")

        if self.rag:
            rag_stats = self.rag.get_stats()
            logger.info("  RAG engine totals:")
            logger.info("    Documents in ChromaDB:  %d", rag_stats.get("document_count", 0))
            logger.info("    Embedding backend:      %s", "Ollama" if rag_stats.get("ollama_embeddings") else "Default/TF-IDF")

        logger.info("")
        logger.info("*" * 60)

    def _save_training_summary(self):
        """Save training summary to a JSON file."""
        summary_dir = os.path.join(PROJECT_ROOT, "logs")
        os.makedirs(summary_dir, exist_ok=True)
        summary_path = os.path.join(
            summary_dir,
            f"mega_train_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )

        try:
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
            logger.info("Training summary saved to: %s", summary_path)
        except Exception as e:
            logger.warning("Failed to save training summary: %s", e)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def list_topics():
    """Print all available domains and topics."""
    print("\nBruce AI - Available Training Topics")
    print("=" * 60)

    grand_total = 0
    for domain, sources in SOURCES.items():
        wiki_count = len(sources.get("wikipedia", []))
        inv_count = len(sources.get("investopedia", []))
        domain_total = wiki_count + inv_count
        grand_total += domain_total

        print(f"\n  [{domain.upper()}] ({domain_total} articles)")
        print(f"  {'─' * 50}")

        if sources.get("wikipedia"):
            print(f"    Wikipedia ({wiki_count}):")
            for article in sources["wikipedia"]:
                display = article.replace("_", " ").replace("%E2%80%93", "-")
                print(f"      - {display}")

        if sources.get("investopedia"):
            print(f"    Investopedia ({inv_count}):")
            for slug in sources["investopedia"]:
                display = slug.replace("-", " ").title()
                print(f"      - {display}")

    print(f"\n{'=' * 60}")
    print(f"  TOTAL: {grand_total} articles across {len(SOURCES)} domains")
    print(f"  Domains: {', '.join(SOURCES.keys())}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Bruce AI - Mega Knowledge Training Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/mega_train.py                    # Train all domains
  python scripts/mega_train.py --domain shipping  # Train shipping only
  python scripts/mega_train.py --domain crypto trading  # Train multiple domains
  python scripts/mega_train.py --list             # List all available topics
  python scripts/mega_train.py --dry-run          # Preview what would be fetched
        """,
    )
    parser.add_argument(
        "--domain",
        nargs="+",
        choices=list(SOURCES.keys()),
        help="Train only specific domain(s)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available topics and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fetched without actually ingesting",
    )

    args = parser.parse_args()

    if args.list:
        list_topics()
        return

    if args.dry_run:
        domains = args.domain or list(SOURCES.keys())
        total = 0
        for d in domains:
            if d not in SOURCES:
                continue
            count = sum(len(v) for v in SOURCES[d].values())
            total += count
            print(f"  {d}: {count} articles")
        print(f"\n  Total: {total} articles would be fetched")
        print(f"  Estimated time: ~{total * (REQUEST_DELAY + 1.5):.0f} seconds")
        return

    trainer = MegaTrainer(domains=args.domain)
    trainer.train_all()


if __name__ == "__main__":
    main()
