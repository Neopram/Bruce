"""
Bruce AI -- Web Browser Module

Provides URL fetching, web search (DuckDuckGo), and news headline retrieval.
All functions return clean text suitable for LLM consumption.
"""

import logging
import re
from typing import Dict, List, Optional
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("Bruce.WebBrowser")

DEFAULT_TIMEOUT = 15
MAX_TEXT_LENGTH = 4000

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _clean_text(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
    """Collapse whitespace and truncate to max_length."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_length:
        text = text[:max_length] + "..."
    return text


def _extract_text(html: str, url: str = "") -> str:
    """Extract readable text from HTML, removing scripts/styles/nav."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside",
                      "noscript", "iframe", "svg", "form"]):
        tag.decompose()

    # Try article/main content first
    main = soup.find("article") or soup.find("main") or soup.find("div", {"role": "main"})
    if main:
        text = main.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    return _clean_text(text)


def fetch_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> Dict:
    """
    Fetch a URL and return clean extracted text.

    Returns:
        dict with keys: success, url, title, text, error
    """
    logger.info("Fetching URL: %s", url)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return {
                "success": True,
                "url": url,
                "title": "",
                "text": _clean_text(resp.text),
                "error": None,
            }

        soup = BeautifulSoup(resp.text, "html.parser")
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""
        text = _extract_text(resp.text, url)

        return {
            "success": True,
            "url": url,
            "title": title,
            "text": text,
            "error": None,
        }

    except requests.exceptions.Timeout:
        logger.warning("Timeout fetching %s", url)
        return {"success": False, "url": url, "title": "", "text": "", "error": "Request timed out"}
    except requests.exceptions.ConnectionError as exc:
        logger.warning("Connection error for %s: %s", url, exc)
        return {"success": False, "url": url, "title": "", "text": "", "error": f"Connection error: {exc}"}
    except requests.exceptions.HTTPError as exc:
        logger.warning("HTTP error for %s: %s", url, exc)
        return {"success": False, "url": url, "title": "", "text": "", "error": f"HTTP {resp.status_code}"}
    except Exception as exc:
        logger.error("Unexpected error fetching %s: %s", url, exc)
        return {"success": False, "url": url, "title": "", "text": "", "error": str(exc)}


def search_web(query: str, max_results: int = 8, timeout: int = DEFAULT_TIMEOUT) -> Dict:
    """
    Search the web using DuckDuckGo HTML endpoint (no API key required).

    Returns:
        dict with keys: success, query, results (list of {title, url, snippet}), error
    """
    logger.info("Web search: %s", query)
    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []

        for result_div in soup.select(".result"):
            title_tag = result_div.select_one(".result__a")
            snippet_tag = result_div.select_one(".result__snippet")

            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            href = title_tag.get("href", "")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

            # DuckDuckGo wraps URLs in a redirect; extract the actual URL
            if "uddg=" in href:
                from urllib.parse import parse_qs, urlparse
                parsed = urlparse(href)
                params = parse_qs(parsed.query)
                href = params.get("uddg", [href])[0]

            results.append({
                "title": title,
                "url": href,
                "snippet": snippet[:300],
            })

            if len(results) >= max_results:
                break

        logger.info("Search returned %d results for '%s'", len(results), query)
        return {
            "success": True,
            "query": query,
            "results": results,
            "error": None,
        }

    except requests.exceptions.Timeout:
        logger.warning("Search timed out for query: %s", query)
        return {"success": False, "query": query, "results": [], "error": "Search timed out"}
    except Exception as exc:
        logger.error("Search error for '%s': %s", query, exc)
        return {"success": False, "query": query, "results": [], "error": str(exc)}


def fetch_news(topic: str, max_results: int = 10, timeout: int = DEFAULT_TIMEOUT) -> Dict:
    """
    Fetch news headlines about a topic using DuckDuckGo News.

    Returns:
        dict with keys: success, topic, articles (list of {title, url, source, snippet}), error
    """
    logger.info("Fetching news for topic: %s", topic)
    news_url = f"https://html.duckduckgo.com/html/?q={quote_plus(topic)}&iar=news"

    try:
        resp = requests.get(news_url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        articles = []

        for result_div in soup.select(".result"):
            title_tag = result_div.select_one(".result__a")
            snippet_tag = result_div.select_one(".result__snippet")

            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            href = title_tag.get("href", "")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

            if "uddg=" in href:
                from urllib.parse import parse_qs, urlparse
                parsed = urlparse(href)
                params = parse_qs(parsed.query)
                href = params.get("uddg", [href])[0]

            # Try to extract source from URL domain
            source = ""
            try:
                from urllib.parse import urlparse as _urlparse
                source = _urlparse(href).netloc.replace("www.", "")
            except Exception:
                pass

            articles.append({
                "title": title,
                "url": href,
                "source": source,
                "snippet": snippet[:300],
            })

            if len(articles) >= max_results:
                break

        logger.info("Found %d news articles for '%s'", len(articles), topic)
        return {
            "success": True,
            "topic": topic,
            "articles": articles,
            "error": None,
        }

    except requests.exceptions.Timeout:
        logger.warning("News fetch timed out for topic: %s", topic)
        return {"success": False, "topic": topic, "articles": [], "error": "Request timed out"}
    except Exception as exc:
        logger.error("News fetch error for '%s': %s", topic, exc)
        return {"success": False, "topic": topic, "articles": [], "error": str(exc)}
