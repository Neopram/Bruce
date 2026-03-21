import logging
import jwt
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Query
from app.config.settings import Config
from cryptography.fernet import Fernet

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Security Constants
SECRET_KEY = Config.SECRET_KEY
ALGORITHM = "HS256"
FERNET_KEY = Config.ENCRYPTION_KEY  # Ensure this key is securely stored
fernet = Fernet(FERNET_KEY)

class WebSocketSecurity:
    """
    Implements security measures for WebSocket connections, including authentication and encryption.
    """
    active_connections = set()

    @staticmethod
    async def connect(websocket: WebSocket, token: str):
        """Authenticates and adds new WebSocket connections."""
        payload = WebSocketSecurity.validate_token(token)
        if not payload:
            await websocket.close(code=1008)
            return
        await websocket.accept()
        WebSocketSecurity.active_connections.add(websocket)
        logging.info(f"✅ WebSocket connection established for user {payload['sub']}")

    @staticmethod
    def validate_token(token: str):
        """Validates JWT tokens for WebSocket connections."""
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            logging.warning("⚠️ Token expired.")
            return None
        except jwt.InvalidTokenError:
            logging.warning("❌ Invalid token.")
            return None

    @staticmethod
    async def disconnect(websocket: WebSocket):
        """Removes WebSocket connection upon disconnection."""
        WebSocketSecurity.active_connections.remove(websocket)
        logging.info("🔴 WebSocket disconnected.")

    @staticmethod
    def encrypt_message(message: str) -> str:
        """Encrypts a message before sending over WebSocket."""
        return fernet.encrypt(message.encode()).decode()

    @staticmethod
    def decrypt_message(encrypted_message: str) -> str:
        """Decrypts a received WebSocket message."""
        return fernet.decrypt(encrypted_message.encode()).decode()

# Example Usage in FastAPI
from fastapi import FastAPI

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """Secure WebSocket endpoint with authentication and encryption."""
    await WebSocketSecurity.connect(websocket, token)
    try:
        while True:
            encrypted_message = await websocket.receive_text()
            message = WebSocketSecurity.decrypt_message(encrypted_message)
            logging.info(f"📩 Received WebSocket message: {message}")
            encrypted_response = WebSocketSecurity.encrypt_message(f"🔄 Echo: {message}")
            await websocket.send_text(encrypted_response)
    except WebSocketDisconnect:
        await WebSocketSecurity.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)