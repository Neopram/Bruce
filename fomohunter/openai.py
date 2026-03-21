import openai
import json
import logging
from pathlib import Path

# Configuración del logger
logging.basicConfig(
    filename="logs/openai.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_config():
    """
    Carga la configuración desde el archivo config.json.

    Returns:
        dict: Configuración cargada.
    """
    config_path = Path("config.json")
    if not config_path.exists():
        logging.error("Archivo config.json no encontrado.")
        raise FileNotFoundError("config.json no encontrado.")

    try:
        with config_path.open("r") as file:
            config = json.load(file)
        # Validar claves importantes
        required_keys = ["openai_api_key", "solana_node", "telegram_token"]
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            logging.error(f"Faltan claves requeridas en config.json: {missing_keys}")
            raise KeyError(f"Claves faltantes: {missing_keys}")
        return config
    except json.JSONDecodeError as e:
        logging.error(f"Error al decodificar config.json: {e}")
        raise

# Cargar configuración
config = load_config()

# Configuración de OpenAI
try:
    openai.api_key = config["openai_api_key"]
    logging.info("Clave API de OpenAI configurada correctamente.")
except KeyError:
    logging.error("Clave API de OpenAI no encontrada en la configuración.")
    raise

def call_openai_chat(prompt):
    """
    Realiza una llamada al modelo de chat de OpenAI.

    Args:
        prompt (str): Texto que se enviará al modelo.

    Returns:
        str: Respuesta generada por OpenAI.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        message = response["choices"][0]["message"]["content"]
        logging.info("Respuesta de OpenAI generada correctamente.")
        return message
    except Exception as e:
        logging.error(f"Error al llamar a OpenAI: {e}", exc_info=True)
        raise
