import dash
import dash_core_components as dcc
import dash_html_components as html
import requests
import json
import logging
from dash.dependencies import Input, Output, State

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# FastAPI Order Execution Endpoint
ORDER_API_URL = "http://localhost:8000/api/order"
AUTH_TOKEN = "your_jwt_token_here"  # Replace with a valid JWT token

# Initialize Dash App
app = dash.Dash(__name__, title="Trade Execution Panel", external_stylesheets=["https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.min.css"])

# -------------------- Dashboard Layout -------------------- #
app.layout = html.Div([
    html.H1("OKK Gorilla Bot - Trade Execution", style={"textAlign": "center"}),

    # Order Type Selection
    html.Label("Select Order Type:"),
    dcc.RadioItems(
        id="order-side",
        options=[{"label": "Buy", "value": "BUY"}, {"label": "Sell", "value": "SELL"}],
        value="BUY",
        labelStyle={"display": "inline-block", "margin-right": "10px"}
    ),

    # Trade Amount
    html.Label("Enter Trade Amount:"),
    dcc.Input(id="trade-amount", type="number", value=1.0, min=0.1, step=0.1),

    # Price Input (Optional)
    html.Label("Enter Price (0 for Market Order):"),
    dcc.Input(id="trade-price", type="number", value=0, min=0, step=0.1),

    # Submit Trade Button
    html.Button("Execute Trade", id="execute-trade", n_clicks=0, style={"margin-top": "10px"}),

    # Trade Execution Result
    html.Div(id="trade-result", style={"margin-top": "20px", "font-weight": "bold"}),

    # Live Trade Logs
    html.Div([
        html.H3("Live Trade Execution Log", style={"textAlign": "center"}),
        dcc.Textarea(id="trade-log", value="", style={"width": "100%", "height": "200px"})
    ]),

    # Refresh Interval
    dcc.Interval(id="interval-update", interval=3000, n_intervals=0),
])


# -------------------- Dashboard Callbacks -------------------- #
@app.callback(
    Output("trade-result", "children"),
    Output("trade-log", "value"),
    Input("execute-trade", "n_clicks"),
    State("order-side", "value"),
    State("trade-amount", "value"),
    State("trade-price", "value"),
    State("trade-log", "value"),
)
def execute_trade(n_clicks, side, amount, price, log_text):
    """
    Sends trade execution requests to FastAPI.
    """
    if n_clicks == 0:
        return "", log_text

    payload = {"side": side, "amount": amount, "price": price}
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}", "Content-Type": "application/json"}

    try:
        response = requests.post(ORDER_API_URL, json=payload, headers=headers)

        if response.status_code == 200:
            trade_response = response.json()
            message = f"✅ Trade Executed: {trade_response}"
        else:
            message = f"❌ Trade Failed: {response.json().get('detail', 'Unknown error')}"

    except Exception as e:
        message = f"🚨 Error executing trade: {e}"

    log_text += f"\n{message}"
    return message, log_text


# -------------------- Run Server -------------------- #
if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
