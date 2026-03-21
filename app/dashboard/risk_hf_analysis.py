import dash
import dash_core_components as dcc
import dash_html_components as html
import requests
import numpy as np
import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objs as go
import logging
from dash.dependencies import Input, Output

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# FastAPI Risk Analytics Endpoint
RISK_API_URL = "http://localhost:8000/api/risk/high_freq"
AUTH_TOKEN = "your_jwt_token_here"  # Replace with a valid JWT token

# Initialize Dash App
app = dash.Dash(__name__, title="High-Frequency Risk & Market Analytics", external_stylesheets=["https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.min.css"])

# -------------------- Dashboard Layout -------------------- #
app.layout = html.Div([
    html.H1("OKK Gorilla Bot - High-Frequency Risk & Market Analytics", style={"textAlign": "center"}),

    # Stress Testing Dashboard
    html.Div([
        html.H3("Stress Testing Across Market Conditions", style={"textAlign": "center"}),
        dcc.Graph(id="stress-test-chart"),
    ]),

    # Scenario Analysis
    html.Div([
        html.H3("Black Swan Event Simulations", style={"textAlign": "center"}),
        dcc.Graph(id="scenario-analysis-chart"),
    ]),

    # Liquidity Risk Monitoring
    html.Div([
        html.H3("Liquidity Risk & Market Depth Analysis", style={"textAlign": "center"}),
        dcc.Graph(id="liquidity-risk-chart"),
    ]),

    # Real-Time Sentiment & News Impact
    html.Div([
        html.H3("Sentiment & Market News Impact", style={"textAlign": "center"}),
        dcc.Graph(id="sentiment-news-chart"),
    ]),

    # Volatility Surface Mapping
    html.Div([
        html.H3("Volatility Surface Mapping", style={"textAlign": "center"}),
        dcc.Graph(id="volatility-surface-chart"),
    ]),

    # Credit & Counterparty Risk
    html.Div([
        html.H3("Credit & Counterparty Risk Monitoring", style={"textAlign": "center"}),
        dcc.Graph(id="counterparty-risk-chart"),
    ]),

    # AI-Generated Crisis Alerts
    html.Div([
        html.H3("AI Market Crisis Prediction", style={"textAlign": "center"}),
        dcc.Graph(id="market-crisis-chart"),
    ]),

    # Auto Refresh Interval
    dcc.Interval(id="interval-update", interval=12000, n_intervals=0),
])


# -------------------- Dashboard Callbacks -------------------- #
@app.callback(
    Output("stress-test-chart", "figure"),
    Output("scenario-analysis-chart", "figure"),
    Output("liquidity-risk-chart", "figure"),
    Output("sentiment-news-chart", "figure"),
    Output("volatility-surface-chart", "figure"),
    Output("counterparty-risk-chart", "figure"),
    Output("market-crisis-chart", "figure"),
    Input("interval-update", "n_intervals"),
)
def update_hf_risk(n):
    """
    Fetches high-frequency risk analytics data from FastAPI.
    """
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    
    try:
        response = requests.get(RISK_API_URL, headers=headers)
        if response.status_code == 200:
            risk_data = response.json()

            # Stress Testing
            stress_figure = {
                "data": [go.Bar(x=risk_data["stress"]["scenarios"], y=risk_data["stress"]["expected_losses"], name="Stress Test")],
                "layout": go.Layout(title="Stress Testing Across Market Conditions", xaxis={"title": "Market Shock"}, yaxis={"title": "Portfolio Loss"})
            }

            # Black Swan Scenario Analysis
            scenario_figure = {
                "data": [go.Scatter(x=risk_data["scenarios"]["timestamps"], y=risk_data["scenarios"]["losses"], mode="lines", name="Scenario Loss")],
                "layout": go.Layout(title="Black Swan Event Simulations", xaxis={"title": "Time"}, yaxis={"title": "Loss Impact"})
            }

            # Liquidity Risk Monitoring
            liquidity_figure = {
                "data": [
                    go.Scatter(x=risk_data["liquidity"]["timestamps"], y=risk_data["liquidity"]["slippage"], mode="lines", name="Slippage"),
                    go.Bar(x=risk_data["liquidity"]["timestamps"], y=risk_data["liquidity"]["market_depth"], name="Market Depth", marker=dict(color="blue"))
                ],
                "layout": go.Layout(title="Liquidity Risk Monitoring", xaxis={"title": "Time"}, yaxis={"title": "Risk Metrics"})
            }

            # Sentiment & Market News Impact
            sentiment_figure = {
                "data": [go.Scatter(x=risk_data["sentiment"]["timestamps"], y=risk_data["sentiment"]["scores"], mode="markers", marker=dict(color="red"))],
                "layout": go.Layout(title="Sentiment & Market News Impact", xaxis={"title": "Time"}, yaxis={"title": "Sentiment Score"})
            }

            # Volatility Surface Mapping
            volatility_figure = {
                "data": [
                    go.Surface(z=risk_data["volatility"]["surface"], x=risk_data["volatility"]["timestamps"], y=risk_data["volatility"]["strikes"])
                ],
                "layout": go.Layout(title="Volatility Surface Mapping", xaxis={"title": "Time"}, yaxis={"title": "Strike Price"}, scene=dict(zaxis={"title": "Volatility"}))
            }

            # Counterparty Risk
            counterparty_figure = {
                "data": [go.Bar(x=risk_data["counterparty"]["entities"], y=risk_data["counterparty"]["risk_scores"], name="Credit Risk", marker=dict(color="orange"))],
                "layout": go.Layout(title="Credit & Counterparty Risk", xaxis={"title": "Entity"}, yaxis={"title": "Risk Score"})
            }

            # AI Crisis Prediction
            crisis_figure = {
                "data": [go.Scatter(x=risk_data["crisis"]["timestamps"], y=risk_data["crisis"]["risk_index"], mode="lines", name="Crisis Risk Index")],
                "layout": go.Layout(title="AI Market Crisis Prediction", xaxis={"title": "Time"}, yaxis={"title": "Crisis Probability"})
            }

            return stress_figure, scenario_figure, liquidity_figure, sentiment_figure, volatility_figure, counterparty_figure, crisis_figure

        return {}, {}, {}, {}, {}, {}, {}

    except Exception as e:
        logging.error(f"🚨 High-Frequency Risk Analytics API Error: {e}")
        return {}, {}, {}, {}, {}, {}, {}


# -------------------- Run Server -------------------- #
if __name__ == "__main__":
    app.run_server(debug=True, port=8055)
