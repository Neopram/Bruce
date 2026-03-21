# Módulo puente de memoria cognitiva
# Nota: conexiones reales a Redis, PostgreSQL y FAISS deben añadirse aquí

def get_context_for_user(user_id: str) -> str:
    """
    Simula extracción de contexto para el usuario.
    En producción, combinar:
    - Últimos mensajes (Redis)
    - Estado financiero e interacciones previas (PostgreSQL)
    - Recuerdos semánticos (FAISS)
    """
    # TODO: conectar con Redis, DB y FAISS
    return f"Usuario {user_id}, último estado: activo, perfil riesgo medio, humor positivo."