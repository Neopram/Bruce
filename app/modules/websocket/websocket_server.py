import asyncio
import websockets
import json
import logging

# Configuración del logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class WebSocketServer:
    """
    Servidor WebSocket local para retransmitir datos en tiempo real.
    """
    def __init__(self, host: str = "localhost", port: int = 8765):
        """
        Inicializa el servidor WebSocket.

        Args:
            host (str): Dirección del host donde se ejecutará el servidor.
            port (int): Puerto donde se ejecutará el servidor.
        """
        self.host = host
        self.port = port
        self.clients = set()

    async def handler(self, websocket, path):
        """
        Manejador principal para nuevos clientes WebSocket.

        Args:
            websocket (WebSocketServerProtocol): Objeto del cliente WebSocket.
            path (str): Ruta del cliente conectado.
        """
        logging.info(f"Nuevo cliente conectado: {path}")
        self.clients.add(websocket)
        try:
            async for message in websocket:
                await self.broadcast(message)
        except websockets.ConnectionClosed:
            logging.info(f"Cliente desconectado: {path}")
        finally:
            self.clients.remove(websocket)

    async def broadcast(self, message):
        """
        Retransmite un mensaje a todos los clientes conectados.

        Args:
            message (str): Mensaje a retransmitir.
        """
        logging.info(f"Retransmitiendo mensaje a {len(self.clients)} clientes.")
        if self.clients:  # Evita errores si no hay clientes conectados
            await asyncio.wait([client.send(message) for client in self.clients])

    async def start_server(self):
        """
        Inicia el servidor WebSocket.
        """
        logging.info(f"Iniciando servidor WebSocket en {self.host}:{self.port}")
        async with websockets.serve(self.handler, self.host, self.port):
            await asyncio.Future()  # Mantiene el servidor corriendo


if __name__ == "__main__":
    server = WebSocketServer(host="localhost", port=8765)
    asyncio.run(server.start_server())
