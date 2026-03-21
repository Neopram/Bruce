import numpy as np
import random

def monte_carlo_forecast(price: float, volatility: float, days: int = 30, simulations: int = 1000):
    results = []
    for _ in range(simulations):
        forecast = price
        for _ in range(days):
            forecast *= (1 + np.random.normal(0, volatility))
        results.append(forecast)
    return {
        "mean_projection": round(np.mean(results), 2),
        "std_dev": round(np.std(results), 2),
        "conf_interval": [round(np.percentile(results, 5), 2), round(np.percentile(results, 95), 2)]
    }

def garch_forecast(price_series: list) -> dict:
    # Placeholder lógico: análisis de volatilidad
    volatility_estimate = np.std(price_series[-10:])
    return {
        "volatility": round(volatility_estimate, 4),
        "trend": "up" if price_series[-1] > price_series[-2] else "down"
    }

def lstm_predictor_stub(price_series: list) -> dict:
    # Placeholder hasta que se entrene una red LSTM real
    next_price = price_series[-1] * (1 + random.uniform(-0.02, 0.03))
    return {
        "predicted_next": round(next_price, 2),
        "confidence": round(random.uniform(0.6, 0.95), 2)
    }