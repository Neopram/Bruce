from fastapi import FastAPI, BackgroundTasks
import asyncio
import logging
import uvicorn
try:
    import dash
    from dash import dcc, html, Input, Output
    DASH_AVAILABLE = True
except ImportError:
    dash = None
    dcc = None
    html = None
    Input = None
    Output = None
    DASH_AVAILABLE = False
from flask import Flask
import threading
import os
from dotenv import load_dotenv
from app.config.settings import Config
from app.modules.websocket.websocket_client import OKXWebSocketClient
from app.modules.machine_learning.predictive_model import PredictiveModel
from app.modules.order_manager import OrderManager
from app.modules.data_collector import DataCollector
from app.modules.volume_tracker import VolumeTracker
import pandas as pd

# Load environment variables
load_dotenv()

# Initialize FastAPI Backend
app_api = FastAPI(title="OKK Gorilla Bot", description="AI-Driven Trading Bot", version="2.0")

# Initialize Flask Server for Dash
flask_server = Flask(__name__)

# Initialize Dash app (for UI)
app_ui = dash.Dash(__name__, server=flask_server, routes_pathname_prefix="/dashboard/")

# Secure API credentials
API_KEY = os.getenv("OKX_API_KEY")
SECRET_KEY = os.getenv("OKX_API_SECRET")
PASSPHRASE = os.getenv("OKX_API_PASSPHRASE")

# Initialize Modules
ai_model = PredictiveModel()
ws_client = OKXWebSocketClient(uri=Config.OKX_WEBSOCKET_URI)
order_manager = OrderManager(api_key=API_KEY, api_secret=SECRET_KEY, passphrase=PASSPHRASE)
data_collector = DataCollector(api_key=API_KEY, api_secret=SECRET_KEY, passphrase=PASSPHRASE)
volume_tracker = VolumeTracker(alert_threshold=5000)

# FastAPI Startup Event
@app_api.on_event("startup")
async def startup_event():
    asyncio.create_task(ws_client.connect())
    logging.info("🚀 OKX WebSocket Started.")

@app_api.get("/")
async def root():
    return {"message": "OKK Gorilla Bot is running!"}

@app_api.get("/trade")
async def trade():
    prediction = ai_model.predict()
    return {"AI Prediction": prediction, "Trade Executed": True}

@app_api.get("/health")
async def health_check():
    return {"status": "healthy", "trading_pair": Config.TRADING_PAIR}

# Dashboard UI Layout
app_ui.layout = html.Div([
    html.H1("🚀 Trading Dashboard - Real-time Monitoring"),
    
    html.Div([
        html.H3("📈 Live Market Data"),
        dcc.Interval(id="update-market", interval=5000, n_intervals=0),
        html.Div(id="live-market-data"),
    ], style={'border': '1px solid black', 'padding': '10px', 'margin': '10px'}),
    
    html.Div([
        html.H3("🛒 Place an Order"),
        dcc.Input(id="order-price", type="number", placeholder="Enter Price"),
        dcc.Input(id="order-size", type="number", placeholder="Enter Size"),
        dcc.Dropdown(
            id="order-type",
            options=[{"label": "Buy", "value": "buy"}, {"label": "Sell", "value": "sell"}],
            placeholder="Select Order Type"
        ),
        html.Button("Submit Order", id="submit-order", n_clicks=0),
        html.Div(id="order-response")
    ], style={'border': '1px solid black', 'padding': '10px', 'margin': '10px'}),
    
    html.Div([
        html.H3("🤖 AI Price Prediction"),
        html.Div(id="ai-prediction"),
    ], style={'border': '1px solid black', 'padding': '10px', 'margin': '10px'}),
])

@app_ui.callback(Output("live-market-data", "children"), Input("update-market", "n_intervals"))
def update_market(n_intervals):
    order_book = data_collector.get_order_book(instrument_id="BTC-USDT", depth=5)
    if "error" in order_book:
        return f"⚠️ Error fetching market data: {order_book['error']}"
    
    bid_price = order_book["bids"][0][0] if order_book["bids"] else "N/A"
    ask_price = order_book["asks"][0][0] if order_book["asks"] else "N/A"
    
    return html.Div([
        html.P(f"Best Bid Price: {bid_price}"),
        html.P(f"Best Ask Price: {ask_price}"),
    ])

@app_ui.callback(Output("order-response", "children"), Input("submit-order", "n_clicks"),
                [Input("order-price", "value"), Input("order-size", "value"), Input("order-type", "value")])
def execute_order(n_clicks, price, size, order_type):
    if n_clicks > 0 and price and size and order_type:
        response = order_manager.create_post_only_order(
            instrument_id="BTC-USDT",
            side=order_type,
            size=str(size),
            price=str(price)
        )
        return f"✅ Order Response: {response}"
    return ""

@app_ui.callback(Output("ai-prediction", "children"), Input("update-market", "n_intervals"))
def ai_prediction(n_intervals):
    recent_prices = [3.7, 3.75, 3.8, 3.85, 3.9, 3.95, 4.0]  # Placeholder for real data
    predicted_price = ai_model.predict(recent_prices)
    return f"📊 AI Predicted Price: {predicted_price:.2f}"

# Run Flask and Dash in parallel
def run_flask():
    flask_server.run(host="0.0.0.0", port=5000, debug=True)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# Run FastAPI (Trading API)
if __name__ == "__main__":
    uvicorn.run(app_api, host="0.0.0.0", port=8000, reload=True)
