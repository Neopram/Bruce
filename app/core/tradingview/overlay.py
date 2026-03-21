# API connection to TradingView chart overlays
import time


class TradingViewOverlay:
    """Manages TradingView chart overlays, indicators, and signal markers."""

    def __init__(self):
        self._indicators = {}
        self._signals = []
        self._config = {
            "chart_type": "candlestick",
            "theme": "dark",
            "timezone": "UTC",
            "show_volume": True,
        }

    def add_indicator(self, name, data, color=None, style="line"):
        """Add an indicator overlay to the chart.

        Args:
            name: Indicator name (e.g., 'SMA_20', 'RSI', 'MACD').
            data: List of dicts with 'timestamp' and 'value' keys.
            color: Optional hex color string (default auto-assigned).
            style: Display style - 'line', 'histogram', 'area', 'dots'.
        """
        colors = ["#2196F3", "#FF9800", "#4CAF50", "#E91E63", "#9C27B0", "#00BCD4"]
        if color is None:
            color = colors[len(self._indicators) % len(colors)]

        self._indicators[name] = {
            "name": name,
            "data": data,
            "color": color,
            "style": style,
            "visible": True,
            "added_at": time.time(),
        }
        return {"status": "added", "indicator": name, "points": len(data)}

    def remove_indicator(self, name):
        """Remove an indicator overlay."""
        if name in self._indicators:
            del self._indicators[name]
            return {"status": "removed", "indicator": name}
        return {"error": f"Indicator '{name}' not found"}

    def add_signal(self, timestamp, signal_type, price, label=None):
        """Add a buy/sell signal marker to the chart.

        Args:
            timestamp: Unix timestamp or ISO string.
            signal_type: 'buy', 'sell', 'stop_loss', 'take_profit'.
            price: Price level for the marker.
            label: Optional text label for the signal.
        """
        signal_colors = {
            "buy": "#4CAF50",
            "sell": "#F44336",
            "stop_loss": "#FF9800",
            "take_profit": "#2196F3",
        }
        signal_shapes = {
            "buy": "arrowUp",
            "sell": "arrowDown",
            "stop_loss": "cross",
            "take_profit": "diamond",
        }

        signal = {
            "timestamp": timestamp,
            "type": signal_type,
            "price": price,
            "label": label or signal_type.upper(),
            "color": signal_colors.get(signal_type, "#FFFFFF"),
            "shape": signal_shapes.get(signal_type, "circle"),
        }
        self._signals.append(signal)
        return {"status": "added", "signal": signal}

    def get_overlay_config(self):
        """Return the complete overlay configuration for the frontend chart."""
        return {
            "chart": self._config,
            "indicators": {
                name: {
                    "name": ind["name"],
                    "style": ind["style"],
                    "color": ind["color"],
                    "visible": ind["visible"],
                    "point_count": len(ind["data"]),
                }
                for name, ind in self._indicators.items()
            },
            "signals": self._signals,
            "total_indicators": len(self._indicators),
            "total_signals": len(self._signals),
        }

    def export_pine_script(self, strategy):
        """Generate a PineScript placeholder for the given strategy.

        Args:
            strategy: Dict with 'name', 'indicators', and optional 'params'.
        """
        name = strategy.get("name", "CustomStrategy")
        indicators = strategy.get("indicators", [])
        params = strategy.get("params", {})

        lines = [
            f'//@version=5',
            f'strategy("{name}", overlay=true, default_qty_type=strategy.percent_of_equity, default_qty_value=10)',
            f'',
        ]

        # Add parameter inputs
        for key, value in params.items():
            if isinstance(value, int):
                lines.append(f'{key} = input.int({value}, "{key}")')
            elif isinstance(value, float):
                lines.append(f'{key} = input.float({value}, "{key}")')

        lines.append('')

        # Add indicator calculations
        for ind in indicators:
            ind_name = ind.get("name", "sma").lower()
            period = ind.get("period", 20)
            if "sma" in ind_name:
                lines.append(f'sma_val = ta.sma(close, {period})')
                lines.append(f'plot(sma_val, color=color.blue, title="SMA {period}")')
            elif "ema" in ind_name:
                lines.append(f'ema_val = ta.ema(close, {period})')
                lines.append(f'plot(ema_val, color=color.orange, title="EMA {period}")')
            elif "rsi" in ind_name:
                lines.append(f'rsi_val = ta.rsi(close, {period})')

        lines.extend([
            '',
            '// Strategy logic placeholder',
            '// TODO: Implement entry/exit conditions',
            'longCondition = ta.crossover(ta.sma(close, 14), ta.sma(close, 28))',
            'shortCondition = ta.crossunder(ta.sma(close, 14), ta.sma(close, 28))',
            '',
            'if (longCondition)',
            '    strategy.entry("Long", strategy.long)',
            'if (shortCondition)',
            '    strategy.close("Long")',
        ])

        return "\n".join(lines)

    def set_chart_config(self, **kwargs):
        """Update chart configuration."""
        for key in ("chart_type", "theme", "timezone", "show_volume"):
            if key in kwargs:
                self._config[key] = kwargs[key]
        return self._config
