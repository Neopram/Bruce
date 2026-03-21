import requests
import logging
import time
from datetime import datetime, timedelta
from telegram import Bot

# Configuración del logger
logging.basicConfig(
    filename="logs/utils.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuración del bot de Telegram
TELEGRAM_BOT_TOKEN = "7440694735:AAFouZltnblyopkAWr2Q1g4yOVupQOBg7wk"
DEFAULT_CHAT_ID = "8104357220"  # Reemplaza con tu ID de chat predeterminado


def get_crypto_price(token_name):
    """
    Obtiene el precio actual de un token en USD desde CoinGecko.
    """
    try:
        response = requests.get(
            f"https://api.coingecko.com/api/v3/simple/price?ids={token_name}&vs_currencies=usd",
            timeout=10
        )
        response.raise_for_status()  # Verifica errores HTTP
        data = response.json()
        if token_name in data and "usd" in data[token_name]:
            return data[token_name]["usd"]
        else:
            raise KeyError(f"No se encontró el token {token_name} en la respuesta.")
    except (requests.exceptions.RequestException, KeyError, ValueError) as e:
        logger.error(f"Error al obtener el precio de {token_name}: {e}")
        return None


def send_telegram_message(message, chat_id=None, retry_attempts=3):
    """
    Envía un mensaje a un usuario o grupo de Telegram utilizando el Bot API.
    """
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    chat_id = chat_id or DEFAULT_CHAT_ID

    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}

    for attempt in range(retry_attempts):
        try:
            response = requests.post(api_url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get("ok"):
                logger.info(f"Mensaje enviado correctamente a Telegram: {message}")
                return result
            else:
                raise Exception(f"Error de Telegram: {result.get('description')}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Intento {attempt + 1}/{retry_attempts} fallido al enviar mensaje: {e}")
            time.sleep(2)

    logger.error("No se pudo enviar el mensaje a Telegram después de varios intentos.")
    raise Exception("Error al enviar mensaje a Telegram.")


def filter_top_tokens(tokens, config_threshold):
    """
    Filtra los tokens que cumplen con criterios configurados en el umbral.

    Args:
        tokens (list): Lista de tokens detectados con detalles como volumen y liquidez.
        config_threshold (dict): Umbrales configurados (ej. score, volumen, liquidez).

    Returns:
        list: Lista de tokens que cumplen con los criterios.
    """
    filtered_tokens = []
    for token in tokens:
        try:
            # Verificar criterios
            meets_score = token["score"] >= config_threshold.get("score", 0)
            meets_liquidity = token.get("liquidity", 0) >= config_threshold.get("liquidity", 0)
            meets_volume = token.get("volume", 0) >= config_threshold.get("volume", 0)

            if meets_score and meets_liquidity and meets_volume:
                filtered_tokens.append(token)
            else:
                logger.info(f"Token descartado: {token['name']} | Score: {meets_score}, "
                            f"Liquidity: {meets_liquidity}, Volume: {meets_volume}")
        except KeyError as e:
            logger.warning(f"Token con datos incompletos descartado: {token} | Error: {e}")

    logger.info(f"Tokens filtrados: {filtered_tokens}")
    return filtered_tokens


def notify_user(message, telegram_token=None, chat_id=None):
    """
    Envía un mensaje de notificación al usuario en Telegram.
    """
    telegram_token = telegram_token or TELEGRAM_BOT_TOKEN
    chat_id = chat_id or DEFAULT_CHAT_ID

    try:
        bot = Bot(token=telegram_token)
        bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"Mensaje enviado al usuario: {message}")
    except Exception as e:
        logger.error(f"Error al enviar mensaje a Telegram: {e}", exc_info=True)


def get_historical_market_data(token_symbol, interval="1d", start_date=None, end_date=None):
    """
    Obtiene datos históricos de mercado para un token específico desde una API pública.
    """
    try:
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        api_url = "https://api.coingecko.com/api/v3/coins/{token}/market_chart/range"
        start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())

        response = requests.get(
            api_url.format(token=token_symbol.lower()),
            params={"vs_currency": "usd", "from": start_timestamp, "to": end_timestamp}
        )

        response.raise_for_status()
        data = response.json()

        formatted_data = {
            "prices": [(datetime.fromtimestamp(p[0] / 1000), p[1]) for p in data.get("prices", [])],
            "volumes": [(datetime.fromtimestamp(v[0] / 1000), v[1]) for v in data.get("total_volumes", [])],
            "market_caps": [(datetime.fromtimestamp(m[0] / 1000), m[1]) for m in data.get("market_caps", [])],
        }

        logger.info(f"Datos históricos obtenidos para {token_symbol}: {formatted_data}")
        return formatted_data

    except Exception as e:
        logger.error(f"Error al obtener datos históricos para {token_symbol}: {e}", exc_info=True)
        raise Exception(f"Error al obtener datos históricos para {token_symbol}: {e}")

import requests

def check_dex_health():
    """
    Verifica el estado de los endpoints de las DEX configuradas en el bot.
    Retorna un diccionario con el estado de cada endpoint.
    """
    # Configuración de las DEX
    dex_endpoints = {
        "raydium": {
            "base_url": "https://api.raydium.io",
            "endpoints": ["/markets", "/pools", "/stats"]
        },
        "orca": {
            "base_url": "https://api.orca.so",
            "endpoints": ["/pools", "/info"]
        },
        "jupiter": {
            "base_url": "https://quote-api.jup.ag",
            "endpoints": ["/v1/quote", "/v1/swap"]
        }
    }

    results = {}

    for dex_name, dex_data in dex_endpoints.items():
        base_url = dex_data["base_url"]
        results[dex_name] = {}

        for endpoint in dex_data["endpoints"]:
            url = base_url + endpoint
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    results[dex_name][endpoint] = {
                        "success": True,
                        "data": response.json()  # Intentar parsear JSON si es posible
                    }
                else:
                    results[dex_name][endpoint] = {
                        "success": False,
                        "status_code": response.status_code,
                        "response": response.text
                    }
            except requests.exceptions.RequestException as e:
                results[dex_name][endpoint] = {
                    "success": False,
                    "error": str(e)
                }

    return results
