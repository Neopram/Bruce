# app/core/volatility_guard.py
"""
🛡️ Sistema de defensa que detecta condiciones críticas del mercado 
y bloquea decisiones de trading temporalmente.
"""

import random
from datetime import datetime

def get_market_volatility():
    # Simulación: reemplazar con integración real si se desea
    return random.uniform(0, 1)

def should_guard_activate():
    threshold = 0.7
    vol = get_market_volatility()
    return vol > threshold, vol

def guardian_check():
    activate, vol = should_guard_activate()
    if activate:
        return {
            "guardian_active": True,
            "volatility": vol,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "🚨 Guardian Mode activado por alta volatilidad"
        }
    else:
        return {
            "guardian_active": False,
            "volatility": vol,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "✅ Todo bajo control"
        }
