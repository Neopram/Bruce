"""
Bruce AI -- Web Crawler Module

A focused web crawler that Bruce uses to learn from the internet.
Respects robots.txt, rate limits, and is a good internet citizen.

Components:
    BruceCrawler  - Crawl pages, follow links, learn from content
"""

import hashlib
import logging
import re
import time
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse, quote_plus

logger = logging.getLogger("Bruce.WebCrawler")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_TIMEOUT = 15
MAX_TEXT_LENGTH = 8000         # max chars per page to ingest
MAX_PAGES_PER_CRAWL = 20      # safety limit for recursive crawling
MIN_REQUEST_DELAY = 2.0        # seconds between requests
MAX_DEPTH = 2                  # max link-follow depth

USER_AGENT = "BruceAI/4.0 (+https://github.com/bruce-ai; educational-crawler)"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Domains we should never crawl
BLOCKED_DOMAINS = {
    "facebook.com", "twitter.com", "x.com", "instagram.com",
    "tiktok.com", "linkedin.com",  # social media (require auth)
    "google.com", "bing.com",  # search engines
}

# File extensions to skip
SKIP_EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".mp4", ".mp3",
    ".zip", ".tar", ".gz", ".exe", ".dmg", ".css", ".js",
}


# ============================================================
#  Robots.txt Checker
# ============================================================

class RobotsChecker:
    """Simple robots.txt checker to be a good citizen."""

    def __init__(self):
        self._cache: Dict[str, Optional[str]] = {}

    def can_fetch(self, url: str) -> bool:
        """Check if our user agent is allowed to fetch this URL."""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        if domain not in self._cache:
            self._fetch_robots(domain)

        robots_text = self._cache.get(domain)
        if robots_text is None:
            return True  # No robots.txt = all allowed

        # Very simple check: look for Disallow rules for * or our agent
        path = parsed.path or "/"
        lines = robots_text.lower().split("\n")
        in_relevant_block = False

        for line in lines:
            line = line.strip()
            if line.startswith("user-agent:"):
                agent = line.split(":", 1)[1].strip()
                in_relevant_block = agent == "*" or "bruce" in agent
            elif line.startswith("disallow:") and in_relevant_block:
                disallowed = line.split(":", 1)[1].strip()
                if disallowed and path.startswith(disallowed):
                    return False

        return True

    def _fetch_robots(self, domain: str):
        """Fetch and cache robots.txt for a domain."""
        try:
            import requests
            resp = requests.get(
                f"{domain}/robots.txt",
                timeout=5,
                headers={"User-Agent": USER_AGENT},
            )
            if resp.status_code == 200:
                self._cache[domain] = resp.text
            else:
                self._cache[domain] = None
        except Exception:
            self._cache[domain] = None


# ============================================================
#  BruceCrawler
# ============================================================

class BruceCrawler:
    """Focused web crawler that learns from the internet.

    Features:
        - Crawl single pages or follow links to a configurable depth
        - Search DuckDuckGo and crawl top results
        - Deep-learn from Wikipedia articles
        - Learn financial terms from Investopedia
        - Respects robots.txt, rate limits, blocked domains
        - Ingests all learned content into KnowledgeIngestor + RAG
    """

    def __init__(self):
        self._robots = RobotsChecker()
        self._visited: Set[str] = set()
        self._last_request_time: Dict[str, float] = {}
        self._knowledge_ingestor = None
        self._rag_engine = None

    # ----- lazy loaders ---------------------------------------------------

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

    # ----- rate limiting & safety -----------------------------------------

    def _should_skip(self, url: str) -> bool:
        """Check if a URL should be skipped."""
        parsed = urlparse(url)

        # Skip blocked domains
        domain = parsed.netloc.replace("www.", "")
        if any(blocked in domain for blocked in BLOCKED_DOMAINS):
            return True

        # Skip non-http
        if parsed.scheme not in ("http", "https"):
            return True

        # Skip file extensions
        path_lower = parsed.path.lower()
        if any(path_lower.endswith(ext) for ext in SKIP_EXTENSIONS):
            return True

        # Skip already visited
        if url in self._visited:
            return True

        # Check robots.txt
        if not self._robots.can_fetch(url):
            logger.debug("Blocked by robots.txt: %s", url)
            return True

        return False

    def _rate_limit(self, url: str):
        """Enforce rate limiting per domain."""
        domain = urlparse(url).netloc
        now = time.time()
        last = self._last_request_time.get(domain, 0)
        elapsed = now - last
        if elapsed < MIN_REQUEST_DELAY:
            time.sleep(MIN_REQUEST_DELAY - elapsed)
        self._last_request_time[domain] = time.time()

    # ----- core fetching --------------------------------------------------

    def _fetch_page(self, url: str) -> Optional[Dict]:
        """Fetch a page and extract text. Returns {url, title, text, links}."""
        if self._should_skip(url):
            return None

        self._rate_limit(url)
        self._visited.add(url)

        try:
            from modules.web_browser import fetch_url as wb_fetch
            result = wb_fetch(url, timeout=DEFAULT_TIMEOUT)
            if not result.get("success"):
                return None

            text = result.get("text", "")
            title = result.get("title", "")

            # Extract links for recursive crawling
            links = self._extract_links(url)

            return {
                "url": url,
                "title": title,
                "text": text[:MAX_TEXT_LENGTH],
                "links": links,
            }
        except Exception as e:
            logger.debug("Fetch error for %s: %s", url, e)
            return None

    def _extract_links(self, url: str) -> List[str]:
        """Extract links from a page."""
        try:
            import requests
            from bs4 import BeautifulSoup

            resp = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            links = []
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                full_url = urljoin(url, href)
                parsed = urlparse(full_url)
                # Only keep http(s) links, strip fragments
                if parsed.scheme in ("http", "https"):
                    clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if clean not in self._visited:
                        links.append(clean)
            return links[:50]  # limit links per page
        except Exception:
            return []

    def _ingest_page(self, page: Dict, metadata: Optional[Dict] = None) -> int:
        """Ingest a fetched page into knowledge base + RAG. Returns chunks added."""
        text = page.get("text", "")
        url = page.get("url", "")
        title = page.get("title", "")

        if not text.strip():
            return 0

        meta = {
            "title": title,
            "url": url,
            "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        if metadata:
            meta.update(metadata)

        chunks_added = 0

        # Ingest via KnowledgeIngestor
        ingestor = self._get_ingestor()
        if ingestor:
            result = ingestor.ingest_text(text, source=url, metadata=meta)
            chunks_added = result.get("chunks_added", 0)

        # Also index in RAG
        rag = self._get_rag()
        if rag:
            rag.index_document(text, metadata={"source": url, **meta})

        return chunks_added

    # ----- public API -----------------------------------------------------

    def crawl_and_learn(self, url: str, depth: int = 1) -> Dict:
        """Crawl a URL and optionally follow links.

        Args:
            url: The starting URL to crawl.
            depth: 0 = just this page, 1 = also follow links on the page, etc.

        Returns:
            {pages_crawled, chunks_ingested, pages, summary}
        """
        logger.info("Crawling: %s (depth=%d)", url, depth)
        self._visited.clear()

        pages_crawled = 0
        total_chunks = 0
        page_summaries = []

        # BFS crawl
        queue = [(url, 0)]  # (url, current_depth)

        while queue and pages_crawled < MAX_PAGES_PER_CRAWL:
            current_url, current_depth = queue.pop(0)

            page = self._fetch_page(current_url)
            if page is None:
                continue

            chunks = self._ingest_page(page, metadata={"domain": "crawl", "depth": current_depth})
            total_chunks += chunks
            pages_crawled += 1

            page_summaries.append({
                "url": page["url"],
                "title": page["title"],
                "text_length": len(page["text"]),
                "chunks": chunks,
            })

            # Follow links if we haven't reached max depth
            if current_depth < depth and current_depth < MAX_DEPTH:
                for link in page.get("links", [])[:10]:  # limit links per page
                    if not self._should_skip(link):
                        queue.append((link, current_depth + 1))

        logger.info("Crawled %d pages, ingested %d chunks", pages_crawled, total_chunks)

        return {
            "url": url,
            "depth": depth,
            "pages_crawled": pages_crawled,
            "chunks_ingested": total_chunks,
            "pages": page_summaries,
        }

    def learn_from_search(self, query: str, max_pages: int = 5) -> Dict:
        """Search DuckDuckGo, crawl top results, learn from them.

        Returns:
            {query, pages_crawled, chunks_ingested, summary}
        """
        logger.info("Learning from search: %s", query)
        try:
            from modules.web_browser import search_web
            search_result = search_web(query, max_results=max_pages)
            if not search_result.get("success"):
                return {"error": search_result.get("error", "Search failed"), "query": query}

            total_pages = 0
            total_chunks = 0
            pages = []

            for r in search_result.get("results", [])[:max_pages]:
                url = r.get("url", "")
                if not url or self._should_skip(url):
                    continue

                page = self._fetch_page(url)
                if page:
                    chunks = self._ingest_page(page, metadata={
                        "domain": "search_learning",
                        "query": query,
                    })
                    total_chunks += chunks
                    total_pages += 1
                    pages.append({
                        "url": url,
                        "title": page.get("title", ""),
                        "chunks": chunks,
                    })

            return {
                "query": query,
                "pages_crawled": total_pages,
                "chunks_ingested": total_chunks,
                "pages": pages,
            }
        except Exception as e:
            logger.error("Search-and-learn error: %s", e)
            return {"error": str(e), "query": query}

    def learn_from_wikipedia(self, topic: str, follow_links: bool = True) -> Dict:
        """Deep-learn a Wikipedia topic.

        Fetches the main article and optionally follows internal Wikipedia
        links (1 level) to build comprehensive knowledge.

        Returns:
            {topic, pages_crawled, chunks_ingested, pages}
        """
        logger.info("Learning from Wikipedia: %s", topic)

        # Construct Wikipedia URL
        topic_slug = topic.replace(" ", "_")
        wiki_url = f"https://en.wikipedia.org/wiki/{quote_plus(topic_slug)}"

        depth = 1 if follow_links else 0

        # Use crawl_and_learn but filter links to only Wikipedia
        self._visited.clear()
        pages_crawled = 0
        total_chunks = 0
        page_summaries = []

        queue = [(wiki_url, 0)]

        while queue and pages_crawled < MAX_PAGES_PER_CRAWL:
            current_url, current_depth = queue.pop(0)

            page = self._fetch_page(current_url)
            if page is None:
                continue

            chunks = self._ingest_page(page, metadata={
                "domain": "wikipedia",
                "topic": topic,
            })
            total_chunks += chunks
            pages_crawled += 1
            page_summaries.append({
                "url": page["url"],
                "title": page["title"],
                "chunks": chunks,
            })

            # Only follow Wikipedia links
            if current_depth < depth:
                wiki_links = [
                    link for link in page.get("links", [])
                    if "wikipedia.org/wiki/" in link
                    and ":" not in urlparse(link).path.split("/wiki/")[-1]  # skip special pages
                    and not self._should_skip(link)
                ]
                for link in wiki_links[:8]:  # limit to 8 linked articles
                    queue.append((link, current_depth + 1))

        return {
            "topic": topic,
            "source": "wikipedia",
            "pages_crawled": pages_crawled,
            "chunks_ingested": total_chunks,
            "pages": page_summaries,
        }

    def learn_from_investopedia(self, term: str) -> Dict:
        """Learn a financial term from Investopedia.

        Returns:
            {term, url, chunks_ingested, title}
        """
        logger.info("Learning from Investopedia: %s", term)
        term_slug = term.lower().replace(" ", "-")
        url = f"https://www.investopedia.com/terms/{term_slug[0]}/{term_slug}.asp"

        page = self._fetch_page(url)
        if page is None:
            # Try search URL as fallback
            search_url = f"https://www.investopedia.com/search?q={quote_plus(term)}"
            try:
                from modules.web_browser import search_web
                results = search_web(f"investopedia {term}", max_results=3)
                for r in results.get("results", []):
                    if "investopedia.com" in r.get("url", ""):
                        page = self._fetch_page(r["url"])
                        if page:
                            break
            except Exception:
                pass

        if page is None:
            return {"error": f"Could not find Investopedia article for: {term}", "term": term}

        chunks = self._ingest_page(page, metadata={
            "domain": "finance_education",
            "source": "investopedia",
            "term": term,
        })

        return {
            "term": term,
            "url": page["url"],
            "title": page.get("title", ""),
            "chunks_ingested": chunks,
        }

    def get_stats(self) -> Dict:
        """Get crawler statistics."""
        return {
            "pages_visited_this_session": len(self._visited),
            "robots_cache_size": len(self._robots._cache),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_crawler: Optional[BruceCrawler] = None


def get_crawler() -> BruceCrawler:
    """Get or create the singleton BruceCrawler."""
    global _crawler
    if _crawler is None:
        _crawler = BruceCrawler()
    return _crawler
