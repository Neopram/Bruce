
# narrador.py
"""
Módulo de Explicación Cognitiva y Pensamiento Contrafactual
DeepSeek puede explicar decisiones pasadas y simular escenarios alternativos
"""
from datetime import datetime
import random

def explicar_operacion(operacion: dict) -> str:
    razon = operacion.get("razon", "No especificada")
    modelo = operacion.get("modelo", "Desconocido")
    resultado = operacion.get("resultado", "sin resultado")
    fecha = operacion.get("fecha", datetime.utcnow().isoformat())

    return (
        f"📈 El día {fecha}, ejecuté una operación basada en el modelo {modelo}. "
        f"La razón principal fue: {razon}. El resultado obtenido fue: {resultado}."
    )

def contrafactual(operacion: dict) -> str:
    resultado_alternativo = round(random.uniform(-3.0, 5.0), 2)
    decision_alternativa = operacion.get("alternativa", "esperar")
    return (
        f"🤔 Si en lugar de {operacion['decision']} hubiésemos decidido {decision_alternativa}, "
        f"el resultado proyectado habría sido aproximadamente {resultado_alternativo}%."
    )
