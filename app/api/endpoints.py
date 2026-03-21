import logging
import asyncio
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Security
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.modules.websocket.websocket_manager import WebSocketManager
from app.modules.machine_learning.predictive_model import PredictiveModel
from app.modules.order_manager import OrderManager
from app.config.settings import config  # ✅ Accedemos a la instancia

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize FastAPI
app = FastAPI(title="OKK Gorilla Bot API", version="2.1", docs_url="/api/docs")

# Core Components
websocket_manager = WebSocketManager()
predictive_model = PredictiveModel()
order_manager = OrderManager()

# OAuth2 & JWT Configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = config.SECRET_KEY
ALGORITHM = "HS256"

# -------------------- AUTHENTICATION -------------------- #
def verify_token(token: str = Security(oauth2_scheme)):
    """
    JWT Token-based authentication for API endpoints.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")

# -------------------- SCHEMAS -------------------- #
class OrderRequest(BaseModel):
    side: str
    amount: float
    price: float

# -------------------- API ROUTES -------------------- #
@app.get("/api/status", tags=["System"])
async def status():
    """
    ✅ API Status Check.
    """
    return {"status": "Bot is running", "version": "2.1"}

@app.get("/api/config", tags=["System"], dependencies=[Depends(verify_token)])
async def get_config():
    """
    🔧 Get bot configuration settings.
    """
    return {
        "trading_pair": config.TRADING_PAIR,
        "mode": "production" if not config.DEBUG else "simulation",
        "post_only_mode": getattr(config, "POST_ONLY_MODE", False)  # Evita crash si no existe
    }

@app.get("/api/market-prediction", tags=["AI"], dependencies=[Depends(verify_token)])
async def market_prediction():
    """
    📈 Get AI-based market prediction asynchronously.
    """
    try:
        prediction = await asyncio.to_thread(predictive_model.predict)
        return {"prediction": prediction}
    except Exception as e:
        logging.error(f"❌ AI Prediction Error: {str(e)}")
        raise HTTPException(status_code=500, detail="AI prediction failed")

@app.post("/api/order", tags=["Trading"], dependencies=[Depends(verify_token)])
async def place_order(order: OrderRequest):
    """
    📌 Execute a Trade Order with retries.
    """
    try:
        for attempt in range(3):
            try:
                result = await order_manager.create_order(order.side, order.amount, order.price)
                return {"status": "success", "order": result}
            except Exception as retry_error:
                logging.warning(f"⚠️ Order attempt {attempt + 1} failed: {retry_error}")
                await asyncio.sleep(1)
        raise Exception("Max retry attempts reached")
    except Exception as e:
        logging.error(f"❌ Order Placement Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Order execution failed")

@app.get("/api/order-book", tags=["Market"], dependencies=[Depends(verify_token)])
async def order_book():
    """
    📊 Retrieve the latest order book snapshot.
    """
    try:
        order_book_data = websocket_manager.get_order_book()
        return {"order_book": order_book_data}
    except Exception as e:
        logging.error(f"❌ Order Book Fetch Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve order book")

# -------------------- WEBSOCKETS -------------------- #
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    🔄 Live WebSocket Feed for Market Data & Trade Executions.
    """
    await websocket.accept()
    websocket_manager.add_client(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            logging.info(f"📡 WebSocket Message Received: {data}")

            if data.get("action") == "subscribe_order_book":
                order_book_data = websocket_manager.get_order_book()
                await websocket.send_json({"type": "order_book", "data": order_book_data})

            elif data.get("action") == "subscribe_predictions":
                prediction = await asyncio.to_thread(predictive_model.predict)
                await websocket.send_json({"type": "ai_prediction", "data": prediction})
    except WebSocketDisconnect:
        websocket_manager.remove_client(websocket)
        logging.info("❌ WebSocket Client Disconnected")

# -------------------- ERROR HANDLER -------------------- #
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    """
    🚨 Custom Error Handler for API.
    """
    logging.error(f"❌ API Error: {exc.detail}")
    return {"error": exc.detail, "status_code": exc.status_code}
