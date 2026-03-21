import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import asyncio
import websockets
import json
import logging
from dash.dependencies import Input, Output
from threading import Thread

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize Dash App
app = dash.Dash(__name__, external_stylesheets=["https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.min.css"])
app.title = "OKK Gorilla Bot Dashboard"

# WebSocket URL
WEBSOCKET_URL = "ws://localhost:8000/ws"

# Live Data Storage
latest_price = []
latest_times = []
order_book_data = {"bids": [], "asks": []}


# -------------------- WebSocket Listener -------------------- #
def start_websocket_listener():
    async def websocket_handler():
        global latest_price, latest_times, order_book_data

        async with websockets.connect(WEBSOCKET_URL) as websocket:
            await websocket.send(json.dumps({"action": "subscribe_order_book"}))

            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)

                    if data["type"] == "order_book":
                        order_book_data["bids"] = data["data"]["bids"]
                        order_book_data["asks"] = data["data"]["asks"]

                    elif data["type"] == "ai_prediction":
                        latest_price.append(data["data"]["price"])
                        latest_times.append(data["data"]["timestamp"])

                        if len(latest_price) > 100:
                            latest_price.pop(0)
                            latest_times.pop(0)

                except Exception as e:
                    logging.error(f"❌ WebSocket Error: {e}")

    asyncio.run(websocket_handler())


# Start WebSocket Listener in Background
ws_thread = Thread(target=start_websocket_listener, daemon=True)
ws_thread.start()


# -------------------- Dashboard Layout -------------------- #
app.layout = html.Div([
    html.H1("OKK Gorilla Bot - Trading Dashboard", style={"textAlign": "center"}),

    # Live Price Chart
    dcc.Graph(id="live-price-chart"),

    # Order Book Visualization
    html.Div([
        html.H3("Order Book", style={"textAlign": "center"}),
        dcc.Graph(id="order-book"),
    ]),

    # AI Prediction Panel
    html.Div([
        html.H3("AI Market Prediction", style={"textAlign": "center"}),
        dcc.Graph(id="ai-prediction"),
    ]),

    # Refresh Interval
    dcc.Interval(id="interval-update", interval=3000, n_intervals=0),
])


# -------------------- Dashboard Callbacks -------------------- #
@app.callback(
    Output("live-price-chart", "figure"),
    Input("interval-update", "n_intervals"),
)
def update_price_chart(n):
    """
    Updates the live price chart with the latest AI-predicted market data.
    """
    return {
        "data": [go.Scatter(x=latest_times, y=latest_price, mode="lines", name="Predicted Price")],
        "layout": go.Layout(title="Live Market Price (AI Prediction)", xaxis={"title": "Time"}, yaxis={"title": "Price"})
    }


@app.callback(
    Output("order-book", "figure"),
    Input("interval-update", "n_intervals"),
)
def update_order_book(n):
    """
    Updates the order book visualization.
    """
    return {
        "data": [
            go.Bar(x=[b[0] for b in order_book_data["bids"]], y=[b[1] for b in order_book_data["bids"]],
                   name="Bids", marker_color="green"),
            go.Bar(x=[a[0] for a in order_book_data["asks"]], y=[a[1] for a in order_book_data["asks"]],
                   name="Asks", marker_color="red"),
        ],
        "layout": go.Layout(title="Order Book", xaxis={"title": "Price"}, yaxis={"title": "Volume"}, barmode="stack")
    }


@app.callback(
    Output("ai-prediction", "figure"),
    Input("interval-update", "n_intervals"),
)
def update_ai_predictions(n):
    """
    Displays AI predictions in a separate chart.
    """
    return {
        "data": [go.Scatter(x=latest_times, y=latest_price, mode="markers", marker=dict(size=10, color="blue"))],
        "layout": go.Layout(title="AI Prediction Data", xaxis={"title": "Time"}, yaxis={"title": "Predicted Price"})
    }


# -------------------- Run Server -------------------- #
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
