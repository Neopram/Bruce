import sys
import os

# Agregar la raíz del proyecto al PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

import pandas as pd
import logging
import matplotlib.pyplot as plt
import openai  # Cambiamos la referencia correcta
from modules.utils import get_historical_market_data

# Configuración del logger
logger = logging.getLogger("backtesting")
logger.setLevel(logging.DEBUG)  # Ajustar nivel de logs (DEBUG, INFO, etc.)
file_handler = logging.FileHandler("logs/backtesting.log")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Configura tu clave de API de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY", "")

ALLOWED_DECISIONS = {"buy", "sell", "hold"}  # Decisiones válidas

def validate_historical_data(data):
    """
    Valida que los datos históricos contengan las columnas necesarias y no tengan valores faltantes.

    Args:
        data (pd.DataFrame): Datos históricos cargados.

    Returns:
        pd.DataFrame: Datos validados y limpios.
    """
    required_columns = {"time", "price", "volume"}
    missing_columns = required_columns - set(data.columns)

    if missing_columns:
        logger.error(f"Faltan las siguientes columnas en los datos: {missing_columns}")
        raise ValueError(f"Los datos históricos están incompletos. Faltan columnas: {missing_columns}")

    # Eliminar filas con valores faltantes
    clean_data = data.dropna(subset=required_columns)
    if clean_data.empty:
        logger.error("Todos los datos históricos tienen valores faltantes. No es posible continuar.")
        raise ValueError("Datos históricos inválidos: Todas las filas están incompletas.")

    logger.info(f"Datos históricos validados: {len(clean_data)} filas disponibles.")
    return clean_data

def execute_trade_simulation(config):
    """
    Simula un flujo de trading usando la configuración proporcionada.

    Args:
        config (dict): Configuración para la simulación.

    Returns:
        dict: Resultados de la simulación.
    """
    # Lógica de la simulación aquí
    return {"status": "success", "message": "Simulación completada"}


def simulate_trades(historical_data, initial_balance, slippage=0.005):
    """
    Simula operaciones de trading basadas en datos históricos.
    """
    logger.info(f"Inicio de simulación con balance inicial: {initial_balance}")
    balance = initial_balance
    position = 0  # Cantidad de tokens en posición
    trades = []

    for index, row in historical_data.iterrows():
        logger.debug(f"Procesando fila: {row.to_dict()} en {row.name}")
        try:
            # Solicitud al modelo de OpenAI
            ai_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un analista financiero experto."},
                    {"role": "user", "content": f"Analiza los datos de mercado: {row.to_dict()}. ¿Deberíamos comprar, vender o mantener?"}
                ]
            )
            decision = ai_response["choices"][0]["message"]["content"].strip().lower()
            logger.debug(f"Decisión del modelo: {decision}")

            if decision not in ALLOWED_DECISIONS:
                logger.warning(f"Respuesta inesperada del modelo: {decision}. Ignorando esta iteración.")
                continue

            if decision == "buy" and balance > 0:
                token_amount = balance / (row['price'] * (1 + slippage))
                balance -= token_amount * row['price'] * (1 + slippage)
                position += token_amount
                trades.append({"action": "buy", "price": row['price'], "volume": token_amount, "time": row.name})
                logger.info(f"Compra realizada: {token_amount} tokens a {row['price']} USD. Balance actual: {balance}")

            elif decision == "sell" and position > 0:
                balance += position * row['price'] * (1 - slippage)
                trades.append({"action": "sell", "price": row['price'], "volume": position, "time": row.name})
                logger.info(f"Venta realizada: {position} tokens a {row['price']} USD. Balance actual: {balance}")
                position = 0

            elif decision == "hold":
                logger.info("Manteniendo posición. No se realizaron operaciones.")

        except KeyError as e:
            logger.error(f"Error en los datos de entrada: {e}. Iteración saltada.", exc_info=True)
        except Exception as e:
            logger.error(f"Error durante la simulación en {row.name}: {e}", exc_info=True)

    final_balance = balance + (position * historical_data.iloc[-1]['price'] if position > 0 else 0)
    logger.info(f"Simulación completada. Balance final: {final_balance}. Ganancia: {final_balance - initial_balance}")
    return {
        "initial_balance": initial_balance,
        "final_balance": final_balance,
        "profit": final_balance - initial_balance,
        "trades": trades
    }

def load_historical_data(file_path):
    """
    Carga datos históricos de un archivo CSV para simulaciones.

    Args:
        file_path (str): Ruta al archivo CSV.

    Returns:
        pd.DataFrame: Datos históricos validados y listos para la simulación.
    """
    try:
        logger.info(f"Cargando datos históricos desde {file_path}")
        data = pd.read_csv(file_path, parse_dates=["time"], index_col="time")
        logger.info(f"Datos históricos cargados con éxito. Total de filas: {len(data)}")
        return validate_historical_data(data)
    except FileNotFoundError:
        logger.error(f"El archivo {file_path} no se encontró.")
        raise
    except Exception as e:
        logger.error(f"Error al cargar datos históricos: {e}", exc_info=True)
        raise

def plot_simulation_results(results, historical_data):
    """
    Genera un gráfico de los resultados de la simulación.
    """
    try:
        logger.info("Generando gráfico de resultados de simulación.")
        plt.figure(figsize=(12, 6))
        plt.plot(historical_data.index, historical_data['price'], label="Precio del mercado", color="blue")

        for trade in results["trades"]:
            if trade["action"] == "buy":
                plt.scatter(trade["time"], trade["price"], color="green", label="Compra", alpha=0.7)
            elif trade["action"] == "sell":
                plt.scatter(trade["time"], trade["price"], color="red", label="Venta", alpha=0.7)

        plt.title("Resultados de la simulación de trading")
        plt.xlabel("Tiempo")
        plt.ylabel("Precio")
        plt.legend()
        plt.grid()
        plt.show()
        logger.info("Gráfico generado con éxito.")
    except Exception as e:
        logger.error(f"Error al generar gráfico de simulación: {e}", exc_info=True)

def main():
    file_path = "data/historical_data.csv"
    initial_balance = 1000
    try:
        historical_data = load_historical_data(file_path)
        results = simulate_trades(historical_data, initial_balance)
        logger.info(f"Resultados de la simulación: {results}")
        plot_simulation_results(results, historical_data)
    except Exception as e:
        logger.error(f"Error durante la simulación: {e}", exc_info=True)

if __name__ == "__main__":
    main()
