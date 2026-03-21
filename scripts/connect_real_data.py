"""Connect Bruce AI to real data sources.
Tests connectivity and configures data feeds.
Usage: python scripts/connect_real_data.py [--test] [--configure]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONNECTIONS_FILE = DATA_DIR / "connections.json"
ENV_FILE = BASE_DIR / ".env"


# ---------------------------------------------------------------------------
# Data source testers
# ---------------------------------------------------------------------------

def test_ccxt_connectivity() -> dict:
    """Test CCXT connectivity by fetching BTC/USDT ticker from Binance public API."""
    result = {
        "source": "ccxt_binance",
        "display_name": "Binance (CCXT) -- BTC/USDT",
        "status": "disconnected",
        "simulated": True,
        "last_tested": datetime.now(timezone.utc).isoformat(),
        "details": {},
    }

    try:
        import ccxt
    except ImportError:
        result["details"]["error"] = "ccxt not installed (pip install ccxt)"
        print(f"  [SKIP] CCXT not installed -- will simulate market data.")
        return result

    try:
        exchange = ccxt.binance({"enableRateLimit": True})
        ticker = exchange.fetch_ticker("BTC/USDT")
        result["status"] = "connected"
        result["simulated"] = False
        result["details"] = {
            "symbol": ticker.get("symbol"),
            "last_price": ticker.get("last"),
            "volume_24h": ticker.get("quoteVolume"),
            "timestamp": ticker.get("datetime"),
        }
        print(f"  [OK] Binance BTC/USDT -- last price: ${ticker.get('last', 'N/A'):,.2f}")
    except Exception as exc:
        result["details"]["error"] = str(exc)
        print(f"  [FAIL] Binance connectivity error: {exc}")

    return result


def test_news_api_connectivity() -> dict:
    """Test news API connectivity. Uses newsapi.org key from env, or simulates."""
    result = {
        "source": "newsapi",
        "display_name": "NewsAPI.org",
        "status": "disconnected",
        "simulated": True,
        "last_tested": datetime.now(timezone.utc).isoformat(),
        "details": {},
    }

    api_key = os.environ.get("NEWSAPI_KEY", "")
    if not api_key:
        result["details"]["info"] = "No NEWSAPI_KEY in environment. Set it in .env to enable."
        print(f"  [SKIP] NEWSAPI_KEY not set -- will simulate news data.")
        return result

    try:
        import requests
        resp = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"country": "us", "pageSize": 1, "apiKey": api_key},
            timeout=10,
        )
        data = resp.json()
        if data.get("status") == "ok":
            result["status"] = "connected"
            result["simulated"] = False
            articles = data.get("articles", [])
            result["details"] = {
                "total_results": data.get("totalResults", 0),
                "sample_headline": articles[0]["title"] if articles else None,
            }
            print(f"  [OK] NewsAPI connected -- {data.get('totalResults', 0)} headlines available.")
        else:
            result["details"]["error"] = data.get("message", "Unknown error")
            print(f"  [FAIL] NewsAPI returned error: {data.get('message')}")
    except ImportError:
        result["details"]["error"] = "requests library not installed"
        print(f"  [SKIP] requests not installed -- cannot test NewsAPI.")
    except Exception as exc:
        result["details"]["error"] = str(exc)
        print(f"  [FAIL] NewsAPI connectivity error: {exc}")

    return result


def test_general_http() -> dict:
    """Basic HTTP connectivity check (can we reach the internet at all?)."""
    result = {
        "source": "http_general",
        "display_name": "General HTTP Connectivity",
        "status": "disconnected",
        "simulated": False,
        "last_tested": datetime.now(timezone.utc).isoformat(),
        "details": {},
    }

    try:
        import urllib.request
        start = time.time()
        urllib.request.urlopen("https://httpbin.org/get", timeout=10)
        elapsed = time.time() - start
        result["status"] = "connected"
        result["details"]["latency_ms"] = round(elapsed * 1000)
        print(f"  [OK] HTTP connectivity OK (latency: {result['details']['latency_ms']} ms)")
    except Exception as exc:
        result["details"]["error"] = str(exc)
        print(f"  [FAIL] No internet connectivity: {exc}")

    return result


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_INTERVALS = {
    "ccxt_binance": {"refresh_seconds": 30, "description": "Crypto ticker refresh"},
    "newsapi": {"refresh_seconds": 900, "description": "News headlines refresh (15 min)"},
}


def save_connections(connections: list[dict]):
    """Save connection status to data/connections.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "connections": connections,
        "refresh_intervals": DEFAULT_INTERVALS,
    }
    with open(CONNECTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\n[SAVED] Connection status -> {CONNECTIONS_FILE}")


def configure_env(connections: list[dict]):
    """Append recommended .env lines for data sources."""
    lines_to_add = []

    # Suggest keys that are missing
    news_conn = next((c for c in connections if c["source"] == "newsapi"), None)
    if news_conn and news_conn["simulated"]:
        lines_to_add.append("# Get a free key at https://newsapi.org/register")
        lines_to_add.append("# NEWSAPI_KEY=your_key_here")

    lines_to_add.append("")
    lines_to_add.append("# Data refresh intervals (seconds)")
    lines_to_add.append("CRYPTO_REFRESH_INTERVAL=30")
    lines_to_add.append("NEWS_REFRESH_INTERVAL=900")

    if not lines_to_add:
        print("\n[CONFIG] No additional .env entries needed.")
        return

    # Read existing .env to avoid duplicates
    existing = ""
    if ENV_FILE.exists():
        existing = ENV_FILE.read_text(encoding="utf-8")

    new_lines = []
    for line in lines_to_add:
        key = line.split("=")[0].strip().lstrip("# ") if "=" in line else None
        if key and key in existing:
            continue
        new_lines.append(line)

    if not new_lines:
        print("\n[CONFIG] .env already has all recommended entries.")
        return

    with open(ENV_FILE, "a", encoding="utf-8") as f:
        f.write("\n# --- Bruce AI Data Connections ---\n")
        for line in new_lines:
            f.write(line + "\n")

    print(f"\n[CONFIG] Appended data-connection settings to {ENV_FILE}")


def print_status_report(connections: list[dict]):
    """Print a summary table."""
    print(f"\n{'='*60}")
    print("  Bruce AI -- Data Connection Status Report")
    print(f"{'='*60}")
    for conn in connections:
        icon = "LIVE" if conn["status"] == "connected" else "SIM "
        print(f"  [{icon}] {conn['display_name']:40s} {conn['status']}")
    live = sum(1 for c in connections if c["status"] == "connected")
    sim = sum(1 for c in connections if c["status"] != "connected")
    print(f"{'='*60}")
    print(f"  Connected: {live}   |   Simulated/Offline: {sim}")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Connect Bruce AI to real data sources.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/connect_real_data.py --test
  python scripts/connect_real_data.py --configure
  python scripts/connect_real_data.py --test --configure
        """,
    )
    parser.add_argument("--test", action="store_true", help="Test connectivity to all data sources")
    parser.add_argument("--configure", action="store_true", help="Save config to .env and data/connections.json")

    args = parser.parse_args()

    # Default to --test if no flags given
    if not args.test and not args.configure:
        args.test = True

    connections = []

    if args.test or args.configure:
        print("\nTesting data source connectivity ...\n")
        connections.append(test_general_http())
        connections.append(test_ccxt_connectivity())
        connections.append(test_news_api_connectivity())

        # Always save connection status
        save_connections(connections)
        print_status_report(connections)

    if args.configure:
        configure_env(connections)
        print("\n[DONE] Configuration complete. Re-run with --test to verify.")


if __name__ == "__main__":
    main()
