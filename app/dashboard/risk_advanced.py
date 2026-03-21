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
RISK_API_URL = "http://localhost:8000/api/risk/advanced"
AUTH_TOKEN = "your_jwt_token_here"  # Replace with a valid JWT token

# Initialize Dash App
app = dash.Dash(__name__, title="Advanced Risk Analytics", external_stylesheets=["https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.min.css"])

# -------------------- Dashboard Layout -------------------- #
app.layout = html.Div([
    html.H1("OKK Gorilla Bot - Advanced Risk Analytics", style={"textAlign": "center"}),

    # Monte Carlo Simulation
    html.Div([
        html.H3("Monte Carlo Simulation (Future Price Paths)", style={"textAlign": "center"}),
        dcc.Graph(id="monte-carlo-chart"),
    ]),

    # Tail Risk Analysis (CVaR)
    html.Div([
        html.H3("Tail Risk Analysis (Conditional VaR)", style={"textAlign": "center"}),
        dcc.Graph(id="tail-risk-chart"),
    ]),

    # Drawdown Recovery Estimations
    html.Div([
        html.H3("Drawdown Recovery Estimations", style={"textAlign": "center"}),
        dcc.Graph(id="drawdown-recovery-chart"),
    ]),

    # Correlation Heatmap
    html.Div([
        html.H3("Portfolio Risk Diversification (Correlation Heatmap)", style={"textAlign": "center"}),
        dcc.Graph(id="correlation-heatmap"),
    ]),

    # Auto Refresh Interval
    dcc.Interval(id="interval-update", interval=10000, n_intervals=0),
])


# -------------------- Dashboard Callbacks -------------------- #
@app.callback(
    Output("monte-carlo-chart", "figure"),
    Output("tail-risk-chart", "figure"),
    Output("drawdown-recovery-chart", "figure"),
    Output("correlation-heatmap", "figure"),
    Input("interval-update", "n_intervals"),
)
def update_advanced_risk(n):
    """
    Fetches advanced risk analytics data from FastAPI.
    """
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    
    try:
        response = requests.get(RISK_API_URL, headers=headers)
        if response.status_code == 200:
            risk_data = response.json()

            # Monte Carlo Simulation
            monte_carlo_figure = {
                "data": [
                    go.Scatter(x=risk_data["monte_carlo"]["time"], y=path, mode="lines", opacity=0.3)
                    for path in risk_data["monte_carlo"]["simulated_paths"]
                ],
                "layout": go.Layout(title="Monte Carlo Simulated Price Paths", xaxis={"title": "Time"}, yaxis={"title": "Price"})
            }

            # Tail Risk Analysis (CVaR)
            tail_risk_figure = {
                "data": [
                    go.Bar(x=risk_data["cvar"]["confidence_levels"], y=risk_data["cvar"]["expected_shortfall"], name="CVaR", marker=dict(color="red"))
                ],
                "layout": go.Layout(title="Conditional Value-at-Risk (CVaR)", xaxis={"title": "Confidence Level"}, yaxis={"title": "Expected Loss"})
            }

            # Drawdown Recovery Estimations
            drawdown_figure = {
                "data": [
                    go.Scatter(x=risk_data["drawdown_recovery"]["timestamps"], y=risk_data["drawdown_recovery"]["recovery_time"], mode="lines+markers", name="Recovery Time")
                ],
                "layout": go.Layout(title="Drawdown Recovery Estimation", xaxis={"title": "Time"}, yaxis={"title": "Recovery Duration"})
            }

            # Correlation Heatmap
            correlation_matrix = np.array(risk_data["correlation_heatmap"])
            correlation_figure = ff.create_annotated_heatmap(
                z=correlation_matrix, x=risk_data["asset_labels"], y=risk_data["asset_labels"], colorscale="RdBu"
            )
            correlation_figure.update_layout(title="Portfolio Correlation Heatmap")

            return monte_carlo_figure, tail_risk_figure, drawdown_figure, correlation_figure

        return {}, {}, {}, {}

    except Exception as e:
        logging.error(f"🚨 Advanced Risk Analytics API Error: {e}")
        return {}, {}, {}, {}


# -------------------- Run Server -------------------- #
if __name__ == "__main__":
    app.run_server(debug=True, port=8054)
