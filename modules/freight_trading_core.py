"""
Physical commodity trading module.
Tracks freight rates, commodity prices, shipping routes, and trade execution
for physical commodities like crude oil, LNG, copper, and containers.
"""
import random
from datetime import datetime, timedelta


class FreightTradingCore:
    """Core engine for physical commodity and freight trading."""

    def __init__(self):
        self.tracked_routes = ["Gulf Stream", "Hormuz", "Singapore", "Panama"]
        self.assets = ["crude oil", "LNG", "copper", "container cargo"]
        self.trade_log = []
        self.route_conditions = {}
        self.commodity_prices = {}
        self.freight_rates = {}
        self._initialize_market_data()

    def _initialize_market_data(self):
        """Initialize simulated market data."""
        self.commodity_prices = {
            "crude oil": {"price_per_barrel": 78.50, "currency": "USD", "unit": "barrel"},
            "LNG": {"price_per_mmbtu": 3.20, "currency": "USD", "unit": "MMBtu"},
            "copper": {"price_per_ton": 8950.00, "currency": "USD", "unit": "metric_ton"},
            "container cargo": {"price_per_teu": 2100.00, "currency": "USD", "unit": "TEU"},
        }
        self.freight_rates = {
            "Gulf Stream": {"rate_per_ton_nm": 0.045, "avg_transit_days": 14},
            "Hormuz": {"rate_per_ton_nm": 0.062, "avg_transit_days": 21},
            "Singapore": {"rate_per_ton_nm": 0.038, "avg_transit_days": 18},
            "Panama": {"rate_per_ton_nm": 0.055, "avg_transit_days": 12},
        }
        for route in self.tracked_routes:
            self.route_conditions[route] = {
                "status": "open",
                "congestion_level": random.uniform(0, 1),
                "weather_risk": random.choice(["low", "moderate", "high"]),
                "last_updated": datetime.utcnow().isoformat(),
            }

    def forecast_disruption(self):
        """Forecast potential disruptions across shipping routes."""
        disruptions = []
        for route in self.tracked_routes:
            risk_score = random.uniform(0, 1)
            if risk_score > 0.6:
                disruption = {
                    "route": route,
                    "risk_score": round(risk_score, 3),
                    "type": random.choice(["weather", "geopolitical", "congestion", "piracy"]),
                    "estimated_delay_days": random.randint(1, 14),
                    "impact_on_rates_pct": round(random.uniform(5, 30), 1),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                disruptions.append(disruption)
        if not disruptions:
            return {"status": "clear", "message": "No disruptions detected"}
        return {"status": "alert", "disruptions": disruptions}

    def get_commodity_price(self, asset):
        """Get current price for a commodity."""
        if asset not in self.commodity_prices:
            return {"status": "error", "message": f"Unknown asset: {asset}"}
        price_info = self.commodity_prices[asset].copy()
        variation = random.uniform(-0.02, 0.02)
        price_key = [k for k in price_info if k.startswith("price_")][0]
        price_info[price_key] = round(price_info[price_key] * (1 + variation), 2)
        price_info["asset"] = asset
        price_info["timestamp"] = datetime.utcnow().isoformat()
        return price_info

    def get_freight_rate(self, route):
        """Get current freight rate for a route."""
        if route not in self.freight_rates:
            return {"status": "error", "message": f"Unknown route: {route}"}
        rate_info = self.freight_rates[route].copy()
        congestion = self.route_conditions[route]["congestion_level"]
        rate_info["rate_per_ton_nm"] = round(rate_info["rate_per_ton_nm"] * (1 + congestion * 0.3), 4)
        rate_info["route"] = route
        rate_info["conditions"] = self.route_conditions[route]
        return rate_info

    def execute_trade(self, asset, volume, route=None):
        """Execute a commodity trade with optional route specification."""
        if asset not in self.assets:
            return {"status": "error", "message": "Asset not supported"}

        price_info = self.get_commodity_price(asset)
        price_key = [k for k in price_info if k.startswith("price_")][0]

        trade = {
            "asset": asset,
            "volume": volume,
            "unit_price": price_info[price_key],
            "total_value": round(price_info[price_key] * volume, 2),
            "currency": "USD",
            "route": route or random.choice(self.tracked_routes),
            "status": "executed",
            "timestamp": datetime.utcnow().isoformat(),
        }

        if route:
            freight = self.get_freight_rate(route)
            trade["freight_cost_per_ton_nm"] = freight["rate_per_ton_nm"]
            trade["estimated_transit_days"] = freight["avg_transit_days"]
            eta = datetime.utcnow() + timedelta(days=freight["avg_transit_days"])
            trade["estimated_arrival"] = eta.isoformat()

        self.trade_log.append(trade)
        return trade

    def calculate_shipping_cost(self, asset, volume, route, distance_nm=5000):
        """Calculate total shipping cost for a given route and volume."""
        rate_info = self.get_freight_rate(route)
        if "status" in rate_info and rate_info["status"] == "error":
            return rate_info
        cost = rate_info["rate_per_ton_nm"] * volume * distance_nm
        return {
            "asset": asset,
            "volume_tons": volume,
            "route": route,
            "distance_nm": distance_nm,
            "rate_per_ton_nm": rate_info["rate_per_ton_nm"],
            "total_freight_cost": round(cost, 2),
            "transit_days": rate_info["avg_transit_days"],
        }

    def get_trade_log(self, limit=50):
        """Return recent trade history."""
        return self.trade_log[-limit:]

    def get_market_overview(self):
        """Return complete market overview."""
        return {
            "commodities": {a: self.get_commodity_price(a) for a in self.assets},
            "routes": {r: self.get_freight_rate(r) for r in self.tracked_routes},
            "disruptions": self.forecast_disruption(),
        }
