
# tests/test_ppo.py
import os

def test_ppo_model_loaded():
    model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "q_trading.npy")
    assert os.path.exists(model_path), "Trading model (q_trading.npy) no encontrado"
