import requests
import logging
from modules.utils import filter_top_tokens, send_telegram_message
from modules.trade_execution import place_order, should_execute_trade
from modules.positions_manager import PositionsManager
from modules.market_analysis import get_crypto_price
from modules.config_loader import load_config

def detect_tokens_in_all_dex(config, dex_platforms):
    """
    Detecta tokens en todos los DEX configurados.

    Args:
        config (dict): Configuración del sistema.
        dex_platforms (list): Lista de plataformas DEX para analizar.

    Returns:
        list: Lista de tokens detectados.
    """
    # Simula la detección de tokens en los DEX configurados.
    tokens = [
        {"name": "TokenA", "liquidity": 200000, "volume": 100000, "price_change_24h": 15, "score": 80},
        {"name": "TokenB", "liquidity": 150000, "volume": 80000, "price_change_24h": 5, "score": 70},
    ]
    return filter_top_tokens(tokens, config["threshold"])

def execute_trades_for_tokens(tokens, config):
    """
    Ejecuta operaciones para los tokens detectados.

    Args:
        tokens (list): Lista de tokens detectados.
        config (dict): Configuración del sistema.
    """
    for token in tokens:
        decision = should_execute_trade(token, config)
        if decision == "buy":
            response = place_order(
                dex_name="raydium",
                token=token,
                amount=100,
                slippage=0.5,
                action="buy"
            )
            if response and response.get("status") == "success":
                print(f"Trade ejecutado para {token['name']}: {response}")
            else:
                print(f"Fallo al ejecutar trade para {token['name']}")

def monitor_positions(positions_manager, config):
    """
    Monitorea posiciones abiertas y las ajusta según sea necesario.

    Args:
        positions_manager (PositionManager): Administrador de posiciones.
        config (dict): Configuración del sistema.
    """
    positions = positions_manager.get_all_positions()
    for position in positions:
        current_price = get_crypto_price(position["token_name"])
        if current_price >= position["take_profit"]:
            positions_manager.close_position(position["id"])
            print(f"Take-profit alcanzado para {position['token_name']}. Posición cerrada.")
        elif current_price <= position["stop_loss"]:
            positions_manager.close_position(position["id"])
            print(f"Stop-loss alcanzado para {position['token_name']}. Posición cerrada.")

if __name__ == "__main__":
    config = load_config()
    positions_manager = PositionsManager()

    # Detectar tokens
    detected_tokens = detect_tokens_in_all_dex(config, config["dex_platforms"])
    print(f"Tokens detectados: {detected_tokens}")

    # Ejecutar trades para tokens detectados
    execute_trades_for_tokens(detected_tokens, config)

    # Monitorear posiciones
    monitor_positions(positions_manager, config)

def snipe_tokens(dex_name, token_address, max_slippage):
    """
    Ejecuta la compra rápida de un token en un DEX.
    
    Args:
        dex_name (str): Nombre del DEX.
        token_address (str): Dirección del token a comprar.
        max_slippage (float): Desviación máxima permitida en el precio.

    Returns:
        dict: Detalles de la transacción.
    """
    try:
        logging.info(f"Intentando snipear el token {token_address} en {dex_name} con un slippage máximo de {max_slippage}%")
        dex_url = f"https://api.{dex_name}.com/snipe"
        payload = {
            "token_address": token_address,
            "max_slippage": max_slippage
        }
        response = requests.post(dex_url, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        logging.info(f"Snipe exitoso: {result}")
        send_telegram_message(f"🎯 Token {token_address} sniped con éxito en {dex_name}. Detalles: {result}")
        return result
    except Exception as e:
        logging.error(f"Error al intentar snipear token: {e}", exc_info=True)
        send_telegram_message(f"⚠️ Error al snipear el token {token_address} en {dex_name}: {e}")
        return {"success": False, "error": str(e)}