import json
import logging

def load_config(config_path="config.json"):
    """
    Carga la configuración desde un archivo JSON.

    Args:
        config_path (str): Ruta al archivo JSON de configuración.

    Returns:
        dict: Diccionario con los parámetros de configuración.
    """
    try:
        with open(config_path, "r") as file:
            config = json.load(file)
            logging.info(f"Configuración cargada correctamente desde {config_path}.")
            return config
    except FileNotFoundError:
        logging.error(f"Archivo de configuración {config_path} no encontrado.")
        raise FileNotFoundError(f"Archivo de configuración {config_path} no encontrado.")
    except json.JSONDecodeError as e:
        logging.error(f"Error al analizar JSON en {config_path}: {e}")
        raise ValueError(f"Error al analizar JSON en {config_path}: {e}")
