import asyncio
import websockets
import json
import logging

# Configuración del logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class WebSocketClient:
    """
    Cliente WebSocket avanzado para conectarse a fuentes de datos en tiempo real.
    """
    def __init__(self, uri: str):
        """
        Inicializa el cliente WebSocket.

        Args:
            uri (str): URI del servidor WebSocket externo.
        """
        self.uri = uri

    async def connect(self):
        """
        Conecta al servidor WebSocket y recibe datos en tiempo real.
        """
        async with websockets.connect(self.uri) as websocket:
            logging.info(f"Conectado al WebSocket en {self.uri}")
            while True:
                try:
                    data = await websocket.recv()
                    self.handle_data(data)
                except websockets.ConnectionClosed as e:
                    logging.error(f"Conexión cerrada: {e}")
                    break
                except Exception as e:
                    logging.error(f"Error inesperado: {e}")

    def handle_data(self, data: str):
        """
        Maneja los datos recibidos del servidor WebSocket.

        Args:
            data (str): Mensaje recibido en formato JSON.
        """
        try:
            parsed_data = json.loads(data)
            logging.info(f"Datos recibidos: {parsed_data}")
            # Aquí puedes retransmitir los datos al servidor WebSocket local.
        except json.JSONDecodeError:
            logging.warning("No se pudo decodificar los datos recibidos.")


if __name__ == "__main__":
    client = WebSocketClient(uri="wss://example.com/marketdata")
    asyncio.run(client.connect())
