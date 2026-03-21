import dash
import dash_core_components as dcc
import dash_html_components as html
import requests
import json
import logging
from dash.dependencies import Input, Output, State

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# FastAPI Risk Management Endpoint
RISK_API_URL = "http://localhost:8000/api/risk"
AUTH_TOKEN = "your_jwt_token_here"  # Replace with a valid JWT token

# Initialize Dash App
app = dash.Dash(__name__, title="Risk Management Panel", external_stylesheets=["https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.min.css"])

# -------------------- Dashboard Layout -------------------- #
app.layout = html.Div([
    html.H1("OKK Gorilla Bot - Risk Management", style={"textAlign": "center"}),

    # Current Leverage & Margin
    html.Div([
        html.Label("Current Leverage:"),
        html.Div(id="current-leverage", style={"font-weight": "bold"}),

        html.Label("Margin Level:"),
        html.Div(id="margin-level", style={"font-weight": "bold"}),

        html.Label("Liquidation Risk:"),
        html.Div(id="liquidation-risk", style={"color": "red", "font-weight": "bold"}),
    ], style={"margin-bottom": "20px"}),

    # Stop-Loss & Take-Profit Controls
    html.Label("Set Stop-Loss (% Loss):"),
    dcc.Input(id="stop-loss", type="number", value=2.0, min=0.5, step=0.1),

    html.Label("Set Take-Profit (% Gain):"),
    dcc.Input(id="take-profit", type="number", value=5.0, min=0.5, step=0.1),

    # Enable AI Risk Control
    html.Label("Enable AI Risk Mitigation:"),
    dcc.RadioItems(
        id="ai-risk-control",
        options=[{"label": "Yes", "value": "YES"}, {"label": "No", "value": "NO"}],
        value="YES",
        labelStyle={"display": "inline-block", "margin-right": "10px"}
    ),

    # Save Settings Button
    html.Button("Save Risk Settings", id="save-risk", n_clicks=0, style={"margin-top": "10px"}),

    # Status Message
    html.Div(id="risk-result", style={"margin-top": "20px", "font-weight": "bold"}),

    # Live Risk Monitoring Logs
    html.Div([
        html.H3("Live Risk Monitoring Log", style={"textAlign": "center"}),
        dcc.Textarea(id="risk-log", value="", style={"width": "100%", "height": "200px"})
    ]),

    # Auto-Refresh Interval
    dcc.Interval(id="interval-update", interval=5000, n_intervals=0),
])


# -------------------- Dashboard Callbacks -------------------- #
@app.callback(
    Output("current-leverage", "children"),
    Output("margin-level", "children"),
    Output("liquidation-risk", "children"),
    Output("risk-log", "value"),
    Input("interval-update", "n_intervals"),
    State("risk-log", "value"),
)
def update_risk_monitoring(n, log_text):
    """
    Fetches real-time risk data from FastAPI.
    """
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    try:
        response = requests.get(RISK_API_URL, headers=headers)
        if response.status_code == 200:
            risk_data = response.json()
            leverage = f"{risk_data['leverage']}x"
            margin = f"{risk_data['margin_level']}%"
            liquidation = f"{risk_data['liquidation_risk']}%"

            log_text += f"\nLeverage: {leverage}, Margin: {margin}, Liquidation Risk: {liquidation}"

            return leverage, margin, liquidation, log_text

        return "N/A", "N/A", "N/A", log_text

    except Exception as e:
        logging.error(f"🚨 Risk API Error: {e}")
        return "N/A", "N/A", "N/A", log_text


@app.callback(
    Output("risk-result", "children"),
    Input("save-risk", "n_clicks"),
    State("stop-loss", "value"),
    State("take-profit", "value"),
    State("ai-risk-control", "value"),
)
def save_risk_settings(n_clicks, stop_loss, take_profit, ai_control):
    """
    Saves updated risk management settings via API.
    """
    if n_clicks == 0:
        return ""

    payload = {
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "ai_risk_control": ai_control
    }
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}", "Content-Type": "application/json"}

    try:
        response = requests.post(f"{RISK_API_URL}/settings", json=payload, headers=headers)

        if response.status_code == 200:
            return "✅ Risk settings updated successfully."

        return f"❌ Failed to update settings: {response.json().get('detail', 'Unknown error')}"

    except Exception as e:
        return f"🚨 Error saving risk settings: {e}"


# -------------------- Run Server -------------------- #
if __name__ == "__main__":
    app.run_server(debug=True, port=8052)
