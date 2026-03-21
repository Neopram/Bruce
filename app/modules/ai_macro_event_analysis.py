import logging
import requests
import pandas as pd
from datetime import datetime
from app.modules.sentiment_analysis_engine import SentimentAnalysisEngine

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
MACRO_EVENT_API_URL = "https://api.tradingeconomics.com/calendar?c=YOUR_API_KEY"
HIGH_IMPACT_EVENTS = ["CPI", "GDP", "Interest Rate", "NFP", "Fed Meeting"]

class AIMacroEventAnalysis:
    """
    AI-Powered Macro Event Analysis for Trading Strategy Adjustments.
    """

    def __init__(self):
        """
        Initializes the macro event analysis module.
        """
        self.sentiment_engine = SentimentAnalysisEngine()

    def fetch_macro_events(self):
        """
        Retrieves upcoming macroeconomic events.

        Returns:
            pd.DataFrame: Processed event data.
        """
        response = requests.get(MACRO_EVENT_API_URL)
        if response.status_code == 200:
            events = response.json()
            df = pd.DataFrame(events)
            df = df[df["Event"].isin(HIGH_IMPACT_EVENTS)]
            return df
        return pd.DataFrame()

    def analyze_macro_impact(self):
        """
        Assesses how macroeconomic events impact cryptocurrency markets.
        """
        events_df = self.fetch_macro_events()
        if events_df.empty:
            logging.info("📉 No High-Impact Events Detected.")
            return None

        logging.info("📊 High-Impact Events Identified:")
        logging.info(events_df[["Event", "Date", "Actual", "Forecast"]])

        for _, row in events_df.iterrows():
            event_name = row["Event"]
            forecast = row["Forecast"]
            actual = row["Actual"]

            impact = (actual - forecast) / forecast if forecast else 0
            sentiment_score = self.sentiment_engine.analyze_sentiment()

            logging.info(f"📉 {event_name} Impact: {impact:.2f}, Sentiment Score: {sentiment_score:.2f}")

        return events_df

# Example Usage
if __name__ == "__main__":
    macro_analyzer = AIMacroEventAnalysis()
    macro_analyzer.analyze_macro_impact()
