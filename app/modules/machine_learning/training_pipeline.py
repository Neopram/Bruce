import os
import json
import time
import logging
import asyncio
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score

from app.modules.machine_learning.clustering import ClusteringModel
from app.modules.machine_learning.anomaly_detection import AnomalyDetectionModel
from app.modules.machine_learning.predictive_model import PredictiveModel
from app.modules.machine_learning.reinforcement_learning import ReinforcementLearningAgent
from app.modules.machine_learning.train_model import TrainModel
from app.modules.data_collector import DataCollector
from app.utils.logger import StructuredLogger

# Logger Configuration
logger = StructuredLogger()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
DEFAULT_OUTPUT_DIR = "models"
DEFAULT_DATA_FILE = "./data/raw/historical_data.csv"
HYPERPARAMETER_GRID = {
    "predictive": {"epochs": [50, 100], "batch_size": [32, 64]},
    "reinforcement_learning": {"timesteps": [50000, 100000]}
}


class TrainingPipeline:
    """
    Automated Training Pipeline for Machine Learning & Reinforcement Learning models.
    """

    def __init__(self, model_type: str, data_file: str = DEFAULT_DATA_FILE, output_dir: str = DEFAULT_OUTPUT_DIR, retrain_interval=86400):
        """
        Initializes the training pipeline.

        Args:
            model_type (str): Model type ('clustering', 'anomaly_detection', 'predictive', 'reinforcement_learning').
            data_file (str): Path to historical data.
            output_dir (str): Directory where trained models and results will be saved.
            retrain_interval (int): Time interval for automatic retraining (default: 24 hours).
        """
        self.model_type = model_type
        self.data_file = data_file
        self.output_dir = output_dir
        self.retrain_interval = retrain_interval
        self.data_collector = DataCollector()
        self.trainer = TrainModel()
        os.makedirs(output_dir, exist_ok=True)
        self.data = self.load_data()

    def load_data(self):
        """
        Loads historical data from a CSV file.

        Returns:
            pd.DataFrame: Processed dataset.
        """
        if not os.path.exists(self.data_file):
            logger.error("🚨 Data file not found", data_file=self.data_file)
            raise FileNotFoundError(f"Data file not found: {self.data_file}")

        logger.info("📥 Loading data", data_file=self.data_file)
        data = pd.read_csv(self.data_file)
        
        if "price" not in data.columns:
            logger.error("❌ Missing 'price' column in dataset")
            raise ValueError("Dataset must contain a 'price' column.")

        logger.info("✅ Data loaded successfully", rows=data.shape[0], columns=data.shape[1])
        return data

    def fetch_new_data(self):
        """
        Collects new market data for AI retraining.
        """
        logger.info("📡 Fetching latest market data...")
        market_data = self.data_collector.get_historical_data(symbol="BTC-USDT", timeframe="1h", limit=500)
        
        if "error" in market_data:
            logger.error(f"❌ Failed to fetch market data: {market_data['error']}")
            return False

        df = pd.DataFrame(market_data)
        df.to_csv(self.trainer.data_path, index=False)
        logger.info(f"✅ Market data updated: {self.trainer.data_path}")
        return True

    def preprocess_data(self):
        """
        Splits dataset into training and test sets.

        Returns:
            tuple: (X_train, X_test, y_train, y_test)
        """
        X = self.data.drop(columns=["price"])
        y = self.data["price"]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        logger.info("📊 Data Preprocessed", train_size=X_train.shape[0], test_size=X_test.shape[0])
        return X_train, X_test, y_train, y_test

    def validate_model(self, model, X_test, y_test):
        """
        Validates the trained model.

        Args:
            model: Trained ML model.
            X_test: Test dataset.
            y_test: Ground truth labels.

        Returns:
            dict: Validation metrics.
        """
        predictions = model.predict(X_test)

        if self.model_type == "predictive":
            mse = mean_squared_error(y_test, predictions)
            logger.info("✅ Predictive Model Validation", mse=mse)
            return {"mse": mse}
        
        elif self.model_type in ["clustering", "anomaly_detection"]:
            accuracy = accuracy_score(y_test, predictions)
            logger.info("✅ Model Validation", accuracy=accuracy)
            return {"accuracy": accuracy}
        
        else:
            logger.error("❌ Unsupported model type for validation", model_type=self.model_type)
            raise ValueError(f"Unsupported model type: {self.model_type}")

    def save_results(self, results):
        """
        Saves model validation results.

        Args:
            results (dict): Validation metrics.
        """
        results_file = os.path.join(self.output_dir, f"{self.model_type}_results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=4)

        logger.info("📂 Validation results saved", results_file=results_file)

    async def hyperparameter_tuning(self):
        """
        Performs hyperparameter tuning for the selected model type.
        """
        if self.model_type in HYPERPARAMETER_GRID:
            logger.info(f"⚙️ Running Hyperparameter Tuning for {self.model_type}")
            best_config = None
            best_score = float("inf")

            for params in HYPERPARAMETER_GRID[self.model_type].values():
                if self.model_type == "predictive":
                    X_train, X_test, y_train, y_test = self.preprocess_data()
                    model = PredictiveModel()
                    model.train(pd.concat([X_train, y_train], axis=1), epochs=params["epochs"], batch_size=params["batch_size"])
                    results = self.validate_model(model, X_test, y_test)

                    if results["mse"] < best_score:
                        best_score = results["mse"]
                        best_config = params

                elif self.model_type == "reinforcement_learning":
                    agent = ReinforcementLearningAgent()
                    agent.train(timesteps=params["timesteps"])
                    best_config = params  # Placeholder for future RL evaluation metrics.

            logger.info("🎯 Best Hyperparameter Configuration Found", best_config=best_config)

    async def run_pipeline(self):
        """
        Runs the automated model training pipeline.
        """
        logger.info(f"🚀 Starting Training Pipeline for {self.model_type}")

        if self.model_type == "clustering":
            model = ClusteringModel()
            model.train(self.data)

        elif self.model_type == "anomaly_detection":
            model = AnomalyDetectionModel()
            model.train(self.data)

        elif self.model_type == "predictive":
            X_train, X_test, y_train, y_test = self.preprocess_data()
            model = PredictiveModel()
            model.train(pd.concat([X_train, y_train], axis=1))
            results = self.validate_model(model, X_test, y_test)
            self.save_results(results)

        elif self.model_type == "reinforcement_learning":
            agent = ReinforcementLearningAgent()
            agent.train()

        else:
            logger.error("❌ Unsupported model type", model_type=self.model_type)
            raise ValueError(f"Unsupported model type: {self.model_type}")

        logger.info(f"✅ Training Pipeline Completed for {self.model_type}")

# Example Usage
if __name__ == "__main__":
    pipeline = TrainingPipeline(model_type="predictive")
    asyncio.run(pipeline.run_pipeline())
