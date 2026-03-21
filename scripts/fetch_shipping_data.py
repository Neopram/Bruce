#!/usr/bin/env python3
"""
Bruce AI - Shipping Data Pipeline
Generates realistic simulated shipping data (BDI, container rates, fuel prices)
and saves to CSV files for training.
"""

import argparse
import csv
import math
import os
import sys
from datetime import datetime, timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "shipping")
os.makedirs(DATA_DIR, exist_ok=True)


def generate_baltic_dry_index(days: int, start_date: datetime) -> list:
    """
    Generate realistic Baltic Dry Index (BDI) data.
    BDI typically ranges 300-5000+ with mean-reverting behavior and seasonality.
    """
    np.random.seed(101)
    n = days
    bdi = np.zeros(n)
    bdi[0] = 1500  # starting value

    mean_level = 1500
    mean_reversion_speed = 0.02
    daily_vol = 0.03

    for i in range(1, n):
        # Seasonal component (shipping peaks around Q3-Q4)
        day_of_year = (start_date + timedelta(days=i)).timetuple().tm_yday
        seasonal = 200 * math.sin(2 * math.pi * (day_of_year - 90) / 365)

        # Mean-reverting random walk
        drift = mean_reversion_speed * (mean_level + seasonal - bdi[i - 1])
        shock = daily_vol * bdi[i - 1] * np.random.randn()
        bdi[i] = max(200, bdi[i - 1] + drift + shock)

    # Sub-indices with correlations
    capesize = bdi * (1.2 + 0.3 * np.random.randn(n) * 0.1)
    panamax = bdi * (0.8 + 0.2 * np.random.randn(n) * 0.1)
    supramax = bdi * (0.6 + 0.15 * np.random.randn(n) * 0.1)

    rows = []
    for i in range(n):
        date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        rows.append([
            date,
            round(bdi[i]),
            round(capesize[i]),
            round(panamax[i]),
            round(supramax[i]),
        ])

    return rows


def generate_container_rates(days: int, start_date: datetime) -> list:
    """
    Generate container freight rate data for major trade lanes.
    Rates in USD per TEU (or FEU for some routes).
    """
    np.random.seed(202)
    n = days

    routes = {
        "Shanghai_Rotterdam": {"base": 2500, "vol": 0.02},
        "Shanghai_LosAngeles": {"base": 3000, "vol": 0.025},
        "Shanghai_NewYork": {"base": 4000, "vol": 0.02},
        "Rotterdam_NewYork": {"base": 1800, "vol": 0.015},
        "Ningbo_Rotterdam": {"base": 2400, "vol": 0.02},
    }

    all_rates = {}
    for route, params in routes.items():
        rates = np.zeros(n)
        rates[0] = params["base"]
        for i in range(1, n):
            day_of_year = (start_date + timedelta(days=i)).timetuple().tm_yday
            seasonal = params["base"] * 0.1 * math.sin(2 * math.pi * (day_of_year - 60) / 365)
            drift = 0.005 * (params["base"] + seasonal - rates[i - 1])
            shock = params["vol"] * rates[i - 1] * np.random.randn()
            rates[i] = max(params["base"] * 0.3, rates[i - 1] + drift + shock)
        all_rates[route] = rates

    rows = []
    route_names = list(routes.keys())
    for i in range(n):
        date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        row = [date] + [round(all_rates[r][i], 2) for r in route_names]
        rows.append(row)

    headers = ["date"] + [f"rate_{r}" for r in route_names]
    return rows, headers


def generate_bunker_fuel_prices(days: int, start_date: datetime) -> list:
    """
    Generate bunker fuel price data (USD per metric ton).
    """
    np.random.seed(303)
    n = days

    fuels = {
        "HFO_380": {"base": 450, "vol": 0.015},
        "VLSFO": {"base": 600, "vol": 0.018},
        "LSMGO": {"base": 750, "vol": 0.02},
        "LNG_per_mmbtu": {"base": 12, "vol": 0.03},
    }

    all_prices = {}
    for fuel, params in fuels.items():
        prices = np.zeros(n)
        prices[0] = params["base"]
        for i in range(1, n):
            # Oil price correlation / mean reversion
            drift = 0.01 * (params["base"] - prices[i - 1])
            shock = params["vol"] * prices[i - 1] * np.random.randn()
            prices[i] = max(params["base"] * 0.4, prices[i - 1] + drift + shock)
        all_prices[fuel] = prices

    # Bunker hubs with price differentials
    hubs = {"Singapore": 1.0, "Rotterdam": 0.97, "Fujairah": 0.95, "Houston": 0.98}

    rows = []
    fuel_names = list(fuels.keys())
    hub_names = list(hubs.keys())

    for i in range(n):
        date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        row = [date]
        for fuel in fuel_names:
            row.append(round(all_prices[fuel][i], 2))
        # Add hub differentials for VLSFO
        for hub, mult in hubs.items():
            row.append(round(all_prices["VLSFO"][i] * mult + np.random.randn() * 5, 2))
        rows.append(row)

    headers = ["date"] + [f"price_{f}" for f in fuel_names] + [f"vlsfo_{h}" for h in hub_names]
    return rows, headers


def generate_port_congestion(days: int, start_date: datetime) -> list:
    """Generate port congestion data (vessels waiting, avg wait days)."""
    np.random.seed(404)
    n = days

    ports = {
        "Shanghai": {"base_vessels": 30, "base_wait": 2.0},
        "Singapore": {"base_vessels": 20, "base_wait": 1.5},
        "Rotterdam": {"base_vessels": 15, "base_wait": 1.0},
        "LosAngeles": {"base_vessels": 25, "base_wait": 3.0},
        "Busan": {"base_vessels": 18, "base_wait": 1.5},
    }

    rows = []
    for i in range(n):
        date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        row = [date]
        for port, params in ports.items():
            day_of_year = (start_date + timedelta(days=i)).timetuple().tm_yday
            seasonal = 0.2 * math.sin(2 * math.pi * (day_of_year - 180) / 365)
            vessels = max(0, int(params["base_vessels"] * (1 + seasonal + 0.15 * np.random.randn())))
            wait_days = max(0.1, params["base_wait"] * (1 + seasonal + 0.2 * np.random.randn()))
            row.extend([vessels, round(wait_days, 1)])
        rows.append(row)

    headers = ["date"]
    for port in ports:
        headers.extend([f"{port}_vessels_waiting", f"{port}_avg_wait_days"])

    return rows, headers


def save_csv(rows: list, headers: list, filepath: str):
    """Save rows to CSV file."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Generate shipping data for Bruce AI training")
    parser.add_argument("--days", type=int, default=365, help="Number of days of history")
    args = parser.parse_args()

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=args.days)

    print(f"\n{'='*60}")
    print(f"  Bruce AI - Shipping Data Pipeline")
    print(f"  Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"  Days: {args.days}")
    print(f"{'='*60}\n")

    # Baltic Dry Index
    print("  Generating Baltic Dry Index data...")
    bdi_rows = generate_baltic_dry_index(args.days, start_date)
    bdi_headers = ["date", "bdi", "capesize_index", "panamax_index", "supramax_index"]
    bdi_path = os.path.join(DATA_DIR, "baltic_dry_index.csv")
    save_csv(bdi_rows, bdi_headers, bdi_path)
    print(f"    Saved {len(bdi_rows)} rows to {bdi_path}")

    # Container Rates
    print("  Generating container freight rates...")
    rate_rows, rate_headers = generate_container_rates(args.days, start_date)
    rate_path = os.path.join(DATA_DIR, "container_rates.csv")
    save_csv(rate_rows, rate_headers, rate_path)
    print(f"    Saved {len(rate_rows)} rows to {rate_path}")

    # Bunker Fuel Prices
    print("  Generating bunker fuel prices...")
    fuel_rows, fuel_headers = generate_bunker_fuel_prices(args.days, start_date)
    fuel_path = os.path.join(DATA_DIR, "bunker_fuel_prices.csv")
    save_csv(fuel_rows, fuel_headers, fuel_path)
    print(f"    Saved {len(fuel_rows)} rows to {fuel_path}")

    # Port Congestion
    print("  Generating port congestion data...")
    cong_rows, cong_headers = generate_port_congestion(args.days, start_date)
    cong_path = os.path.join(DATA_DIR, "port_congestion.csv")
    save_csv(cong_rows, cong_headers, cong_path)
    print(f"    Saved {len(cong_rows)} rows to {cong_path}")

    print(f"\n{'='*60}")
    print(f"  Pipeline Complete!")
    print(f"  Output directory: {DATA_DIR}")
    print(f"  Files generated: 4")
    print(f"  Total rows: {len(bdi_rows) + len(rate_rows) + len(fuel_rows) + len(cong_rows)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
