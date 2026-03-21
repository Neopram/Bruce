from fastapi import APIRouter, Form
from typing import List
from .strategy_hub import list_strategies, select_strategy
from .simulator import simulate_strategy
from .quant_predictor import monte_carlo_forecast
from .strategy_evolver import evolve_population

router = APIRouter(prefix="/internal/trading", tags=["Trading Engine"])

price_mock = [100 + i * 0.5 for i in range(60)]  # Series de prueba

@router.get("/strategies")
def get_strategies():
    return list_strategies()

@router.post("/simulate")
def run_simulation(strategy_name: str = Form(...), capital: float = Form(10000.0)):
    return simulate_strategy(price_mock, strategy_name, capital=capital)

@router.get("/predict")
def forecast_market():
    return monte_carlo_forecast(price=100, volatility=0.03)

@router.post("/evolve")
def evolve():
    population = [
        {"name": "mean_reversion", "params": {"capital": 10000.0, "risk": 0.01}},
        {"name": "mean_reversion", "params": {"capital": 9500.0, "risk": 0.02}},
        {"name": "mean_reversion", "params": {"capital": 11000.0, "risk": 0.015}},
    ]
    result = evolve_population(population, simulate_strategy, price_mock)
    return {"best_strategy": result}