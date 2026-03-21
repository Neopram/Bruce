import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
import requests
import json
import logging
from dash.dependencies import Input, Output, State

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# FastAPI Risk Analytics Endpoint
RISK_API_URL = "http://localhost:8000/api/risk/analytics"
AUTH_TOKEN = "your_jwt_token_here"  # Replace with a valid JWT token

# Initialize Dash App
app = dash.Dash(__name__, title="Advanced Risk Analytics", external_stylesheets=["https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.min.css"])

# -------------------- Dashboard Layout -------------------- #
app.layout = html.Div([
    html.H1("OKK Gorilla Bot - Advanced Risk Analytics", style={"textAlign": "center"}),

    # Portfolio Value-at-Risk (VaR)
    html.Div([
        html.H3("Portfolio Value-at-Risk (VaR)", style={"textAlign": "center"}),
        dcc.Graph(id="var-chart"),
    ]),

    # Volatility & Historical Drawdown
    html.Div([
        html.H3("Volatility & Historical Drawdown", style={"textAlign": "center"}),
        dcc.Graph(id="volatility-chart"),
    ]),

    # Risk-Adjusted Performance (Sharpe Ratio)
    html.Div([
        html.H3("Risk-Adjusted Performance (Sharpe Ratio)", style={"textAlign": "center"}),
        dcc.Graph(id="sharpe-ratio-chart"),
    ]),

    # Refresh Interval
    dcc.Interval(id="interval-update", interval=6000, n_intervals=0),
])


# -------------------- Dashboard Callbacks -------------------- #
@app.callback(
    Output("var-chart", "figure"),
    Output("volatility-chart", "figure"),
    Output("sharpe-ratio-chart", "figure"),
    Input("interval-update", "n_intervals"),
)
def update_risk_analytics(n):
    """
    Fetches real-time risk analytics data from FastAPI.
    """
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    
    try:
        response = requests.get(RISK_API_URL, headers=headers)
        if response.status_code == 200:
            risk_data = response.json()

            # Portfolio VaR Calculation
            var_figure = {
                "data": [dict(x=risk_data["var"]["confidence_levels"], y=risk_data["var"]["values"], type="line", name="VaR")],
                "layout": dict(title="Portfolio Value-at-Risk (VaR)", xaxis={"title": "Confidence Level"}, yaxis={"title": "Potential Loss"})
            }

            # Volatility Tracking
            vol_figure = {
                "data": [
                    dict(x=risk_data["volatility"]["timestamps"], y=risk_data["volatility"]["values"], type="line", name="Volatility"),
                    dict(x=risk_data["drawdown"]["timestamps"], y=risk_data["drawdown"]["values"], type="bar", name="Drawdown", marker=dict(color="red"))
                ],
                "layout": dict(title="Volatility & Drawdown", xaxis={"title": "Time"}, yaxis={"title": "Risk Metrics"})
            }

            # Sharpe Ratio & Performance
            sharpe_figure = {
                "data": [dict(x=risk_data["sharpe"]["timestamps"], y=risk_data["sharpe"]["values"], type="scatter", mode="lines+markers", name="Sharpe Ratio")],
                "layout": dict(title="Risk-Adjusted Performance (Sharpe Ratio)", xaxis={"title": "Time"}, yaxis={"title": "Sharpe Ratio"})
            }

            return var_figure, vol_figure, sharpe_figure

        return {}, {}, {}

    except Exception as e:
        logging.error(f"🚨 Risk Analytics API Error: {e}")
        return {}, {}, {}


# -------------------- Run Server -------------------- #
if __name__ == "__main__":
    app.run_server(debug=True, port=8053)
