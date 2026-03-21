import os
import logging
from dotenv import load_dotenv
from app.config.secrets_loader import SecretsLoader

# Cargar variables de entorno
load_dotenv()

# Configuración del logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class FeatureFlags:
    """
    Clase central para manejar las banderas de características (feature flags).
    """
    def __init__(self):
        # Inicialización del cargador de secretos
        self.secrets = SecretsLoader()
        self.flags = self.load_flags()

    def load_flags(self):
        """
        Carga las banderas desde múltiples fuentes, como variables de entorno y secretos.

        Returns:
            dict: Diccionario de banderas de características.
        """
        return {
            "advanced_order_management": self.secrets.get_secret(
                "features.advanced_order_management", 
                os.getenv("ADVANCED_ORDER_MANAGEMENT", "false").lower() == "true"
            ),
            "real_time_notifications": self.secrets.get_secret(
                "features.real_time_notifications",
                os.getenv("REAL_TIME_NOTIFICATIONS", "false").lower() == "true"
            ),
            "ai_risk_analysis": self.secrets.get_secret(
                "features.ai_risk_analysis",
                os.getenv("AI_RISK_ANALYSIS", "false").lower() == "true"
            ),
            "dynamic_throttling": self.secrets.get_secret(
                "features.dynamic_throttling",
                os.getenv("DYNAMIC_THROTTLING", "false").lower() == "true"
            ),
        }

    def is_enabled(self, feature_name):
        """
        Verifica si una bandera de característica está habilitada.

        Args:
            feature_name (str): Nombre de la bandera.

        Returns:
            bool: True si la bandera está habilitada, False en caso contrario.
        """
        return self.flags.get(feature_name, False)

    def log_flags(self):
        """
        Registra las banderas activas en los logs.
        """
        logging.info("=== ESTADO DE LAS BANDERAS DE CARACTERÍSTICAS ===")
        for feature, enabled in self.flags.items():
            logging.info(f"{feature}: {'Habilitado' if enabled else 'Deshabilitado'}")


# Ejemplo de uso
if __name__ == "__main__":
    feature_flags = FeatureFlags()
    feature_flags.log_flags()
    print("Real-Time Notifications Habilitado:", feature_flags.is_enabled("real_time_notifications"))
