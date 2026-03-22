"""
Bruce AI - SEC EDGAR Data Connector
=====================================
Free SEC EDGAR API (no key required).
User-Agent header required by SEC policy.
Responses cached for 60 seconds.
"""

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger("Bruce.EDGAR")

EFTS_BASE = "https://efts.sec.gov/LATEST"
EDGAR_BASE = "https://www.sec.gov"
EDGAR_DATA = "https://data.sec.gov"
REQUEST_TIMEOUT = 20
CACHE_TTL = 60

HEADERS = {
    "User-Agent": "BruceAI federico@example.com",
    "Accept-Encoding": "gzip, deflate",
}


class _Cache:
    """Simple TTL cache."""

    def __init__(self, ttl: int = CACHE_TTL):
        self._store: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        ts = self._timestamps.get(key)
        if ts is not None and (time.time() - ts) < self._ttl:
            return self._store[key]
        self._store.pop(key, None)
        self._timestamps.pop(key, None)
        return None

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value
        self._timestamps[key] = time.time()


_cache = _Cache()

# Rate limiting: SEC asks for max 10 requests/second
_last_request_time: float = 0.0
_MIN_INTERVAL = 0.15  # ~6-7 req/s to stay well under 10/s


def _rate_limit() -> None:
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request_time = time.time()


def _get(url: str, params: Optional[dict] = None) -> Any:
    """Rate-limited, cached GET request with SEC-required headers."""
    cache_key = f"{url}|{json.dumps(params or {}, sort_keys=True)}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    _rate_limit()
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 429:
            logger.warning("SEC EDGAR rate limit hit, backing off 10s")
            time.sleep(10)
            resp = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        if "json" in content_type:
            data = resp.json()
        else:
            data = resp.text
        _cache.set(cache_key, data)
        return data
    except requests.exceptions.Timeout:
        logger.error(f"SEC EDGAR timeout: {url}")
        return {"error": "Request timed out"}
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", "?")
        logger.error(f"SEC EDGAR HTTP {status}: {e}")
        return {"error": f"HTTP {status}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"SEC EDGAR request error: {e}")
        return {"error": str(e)}


def _cik_from_ticker(ticker: str) -> Optional[str]:
    """Resolve a ticker symbol to a CIK number using SEC's company tickers JSON."""
    cache_key = f"cik_lookup|{ticker.upper()}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    data = _get(f"{EDGAR_DATA}/submissions/company_tickers.json")
    if isinstance(data, dict) and "error" not in data:
        for _key, entry in data.items():
            if entry.get("ticker", "").upper() == ticker.upper():
                cik = str(entry["cik_str"]).zfill(10)
                _cache.set(cache_key, cik)
                return cik
    return None


# ===================================================================
#  Public API
# ===================================================================

def search_filings(
    company: str,
    filing_type: str = "10-K",
    start_date: str = "",
    end_date: str = "",
    limit: int = 10,
) -> Dict:
    """Search SEC filings using EDGAR full-text search.

    Args:
        company: Company name or ticker (e.g. 'Apple', 'AAPL')
        filing_type: Filing type filter (e.g. '10-K', '10-Q', '8-K', 'S-1')
        start_date: Start date filter YYYY-MM-DD
        end_date: End date filter YYYY-MM-DD
        limit: Max results (1-100)

    Returns:
        Dict with filing results
    """
    limit = min(max(limit, 1), 100)
    params = {
        "q": company,
        "forms": filing_type,
        "from": 0,
        "size": limit,
    }
    if start_date:
        params["startdt"] = start_date
    if end_date:
        params["enddt"] = end_date

    data = _get(f"{EFTS_BASE}/search-index", params)
    if isinstance(data, str):
        # EFTS might return HTML on error
        return {"error": "Unexpected response from SEC search", "hint": data[:200]}
    if isinstance(data, dict) and "error" in data:
        return data

    hits = data.get("hits", {})
    total = hits.get("total", {}).get("value", 0)
    results = []
    for hit in hits.get("hits", [])[:limit]:
        source = hit.get("_source", {})
        filing_url = ""
        file_num = source.get("file_num", "")
        # Build filing URL if we have enough info
        accession = source.get("_id", "").replace("-", "")
        if accession:
            filing_url = f"{EDGAR_BASE}/Archives/edgar/data/{source.get('entity_id', '')}/{accession}"

        results.append({
            "entity_name": source.get("entity_name", ""),
            "ticker": source.get("tickers", ""),
            "filing_type": source.get("form_type", filing_type),
            "filed_date": source.get("file_date", ""),
            "description": source.get("display_names", [""])[0] if source.get("display_names") else "",
            "file_number": file_num,
            "url": filing_url,
        })

    return {
        "query": company,
        "filing_type": filing_type,
        "total_results": total,
        "results": results,
        "count": len(results),
    }


def get_company_info(ticker: str) -> Dict:
    """Get company details from SEC EDGAR by ticker.

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL', 'MSFT')

    Returns:
        Dict with CIK, company name, SIC, addresses, etc.
    """
    cik = _cik_from_ticker(ticker)
    if not cik:
        return {"error": f"Ticker '{ticker}' not found in SEC database"}

    data = _get(f"{EDGAR_DATA}/submissions/CIK{cik}.json")
    if isinstance(data, dict) and "error" in data:
        return data
    if not isinstance(data, dict):
        return {"error": "Unexpected response format"}

    addresses = data.get("addresses", {})
    business_addr = addresses.get("business", {})
    mailing_addr = addresses.get("mailing", {})

    return {
        "cik": cik,
        "ticker": ticker.upper(),
        "name": data.get("name", ""),
        "entity_type": data.get("entityType", ""),
        "sic": data.get("sic", ""),
        "sic_description": data.get("sicDescription", ""),
        "state_of_incorporation": data.get("stateOfIncorporation", ""),
        "fiscal_year_end": data.get("fiscalYearEnd", ""),
        "ein": data.get("ein", ""),
        "exchanges": data.get("exchanges", []),
        "business_address": {
            "street": business_addr.get("street1", ""),
            "city": business_addr.get("city", ""),
            "state": business_addr.get("stateOrCountry", ""),
            "zip": business_addr.get("zipCode", ""),
        },
        "website": data.get("website", ""),
        "investor_website": data.get("investorWebsite", ""),
        "category": data.get("category", ""),
        "filing_count": len(data.get("filings", {}).get("recent", {}).get("accessionNumber", [])),
    }


def get_recent_filings(ticker: str, limit: int = 10) -> Dict:
    """Get recent filings for a company by ticker.

    Args:
        ticker: Stock ticker symbol
        limit: Number of recent filings to return

    Returns:
        Dict with list of recent filings
    """
    cik = _cik_from_ticker(ticker)
    if not cik:
        return {"error": f"Ticker '{ticker}' not found in SEC database"}

    data = _get(f"{EDGAR_DATA}/submissions/CIK{cik}.json")
    if isinstance(data, dict) and "error" in data:
        return data
    if not isinstance(data, dict):
        return {"error": "Unexpected response format"}

    recent = data.get("filings", {}).get("recent", {})
    accession_numbers = recent.get("accessionNumber", [])
    forms = recent.get("form", [])
    filing_dates = recent.get("filingDate", [])
    primary_docs = recent.get("primaryDocument", [])
    descriptions = recent.get("primaryDocDescription", [])

    filings = []
    for i in range(min(limit, len(accession_numbers))):
        accession = accession_numbers[i]
        accession_no_dash = accession.replace("-", "")
        doc = primary_docs[i] if i < len(primary_docs) else ""
        filing_url = (
            f"{EDGAR_BASE}/Archives/edgar/data/{cik.lstrip('0')}/{accession_no_dash}/{doc}"
            if doc else ""
        )

        filings.append({
            "form": forms[i] if i < len(forms) else "",
            "filed_date": filing_dates[i] if i < len(filing_dates) else "",
            "accession_number": accession,
            "description": descriptions[i] if i < len(descriptions) else "",
            "url": filing_url,
        })

    return {
        "ticker": ticker.upper(),
        "cik": cik,
        "company": data.get("name", ""),
        "filings": filings,
        "count": len(filings),
    }


def get_filing_text(url: str, max_chars: int = 5000) -> Dict:
    """Extract text content from a SEC filing URL.

    Args:
        url: Full URL to a SEC filing document
        max_chars: Maximum characters to return (default 5000)

    Returns:
        Dict with extracted text and metadata
    """
    if not url or not url.startswith(("http://", "https://")):
        return {"error": "Invalid URL. Must be a full SEC filing URL."}

    data = _get(url)
    if isinstance(data, dict) and "error" in data:
        return data

    if not isinstance(data, str):
        return {"error": "Unexpected response type"}

    # Strip HTML tags for readable text
    text = data
    if "<html" in text.lower() or "<body" in text.lower():
        # Simple HTML tag stripping
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"&#\d+;", "", text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()

    truncated = len(text) > max_chars
    text = text[:max_chars]

    return {
        "url": url,
        "text": text,
        "char_count": len(text),
        "truncated": truncated,
    }
