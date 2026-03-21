# 📂 app/api/core_routes.py

import logging
import asyncio
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Security
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

# Internal modules
from app.modules.websocket.websocket_manager import WebSocketManager
from app.modules.machine_learning.predictive_model import PredictiveModel
from app.modules.order_manager import OrderManager
from app.config.settings import Config

router = APIRouter()

# OAuth2 + JWT Auth Setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = Config.SECRET_KEY
ALGORITHM = "HS256"

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# WebSocket manager + AI model
websocket_manager = WebSocketManager()
predictive_model = PredictiveModel()
order_manager = OrderManager()

# -------------------- AUTH UTILITY -------------------- #
def verify_token(token: str = Security(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")

# -------------------- MODELS -------------------- #
class OrderRequest(BaseModel):
    side: str
    amount: float
    price: float

# -------------------- SYSTEM STATUS -------------------- #
@router.get("/status", tags=["System"])
async def status():
    """
    ✅ API Status Check.
    """
    return {"status": "Bot is running", "version": "2.1"}

@router.get("/config", tags=["System"], dependencies=[Depends(verify_token)])
async def get_config():
    """
    🔧 Get bot configuration settings.
    """
    return {
        "trading_pair": Config.TRADING_PAIR,
        "mode": "production" if not Config.DEBUG else "simulation",
        "post_only_mode": Config.POST_ONLY_MODE,
    }

# -------------------- AI PREDICTION -------------------- #
@router.get("/market-prediction", tags=["AI"], dependencies=[Depends(verify_token)])
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

# -------------------- TRADING -------------------- #
@router.post("/order", tags=["Trading"], dependencies=[Depends(verify_token)])
async def place_order(order: OrderRequest):
    """
    📌 Execute a Trade Order with retries.
    """
    try:
        for attempt in range(3):
            try:
                result = order_manager.place_order(order.side, order.amount, order.price)
                return {"status": "success", "order": result}
            except Exception as retry_error:
                logging.warning(f"⚠️ Order attempt {attempt + 1} failed: {retry_error}")
                await asyncio.sleep(1)
        raise Exception("Max retry attempts reached")
    except Exception as e:
        logging.error(f"❌ Order Placement Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Order execution failed")

@router.get("/order-book", tags=["Market"], dependencies=[Depends(verify_token)])
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
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    🔄 Live WebSocket Feed for Market Data & AI Predictions.
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
@router.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    """
    🚨 Custom Error Handler for API.
    """
    logging.error(f"❌ API Error: {exc.detail}")
    return {"error": exc.detail, "status_code": exc.status_code}
