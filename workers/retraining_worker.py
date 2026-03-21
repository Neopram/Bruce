import logging
import os
import pandas as pd
from app.modules.machine_learning.training_pipeline import TrainingPipeline
from app.config.settings import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class RetrainingWorker:
    """
    Worker responsible for automating the retraining of machine learning models.
    """

    def __init__(self):
        """
        Initializes the retraining worker with configurable paths and settings.
        """
        self.training_data_dir = Config.TRAINING_DATA_DIR
        self.models_dir = Config.ML_MODELS_DIR

    def retrain_models(self):
        """
        Retrains all machine learning models with updated data.
        """
        logging.info("Starting model retraining process...")

        # Check if training data directory exists
        if not os.path.exists(self.training_data_dir):
            logging.error(f"Training data directory does not exist: {self.training_data_dir}")
            return

        # Process each dataset in the training data directory
        for file in os.listdir(self.training_data_dir):
            if file.endswith(".csv"):
                file_path = os.path.join(self.training_data_dir, file)
                model_type = self._determine_model_type(file)

                logging.info(f"Retraining model of type '{model_type}' with data: {file_path}")

                try:
                    # Initialize the training pipeline and train the model
                    pipeline = TrainingPipeline(data_file=file_path, model_type=model_type, output_dir=self.models_dir)
                    pipeline.run_pipeline()
                except Exception as e:
                    logging.error(f"Error retraining model for {file}: {e}")

        logging.info("Model retraining process completed.")

    def _determine_model_type(self, filename):
        """
        Determines the model type based on the dataset file name.

        Args:
            filename (str): Name of the dataset file.

        Returns:
            str: Model type (e.g., 'predictive', 'anomaly_detection', etc.).
        """
        if "predictive" in filename.lower():
            return "predictive"
        elif "anomaly" in filename.lower():
            return "anomaly_detection"
        elif "clustering" in filename.lower():
            return "clustering"
        elif "reinforcement" in filename.lower():
            return "reinforcement_learning"
        else:
            raise ValueError(f"Unknown model type for file: {filename}")


# Entry point for standalone execution
if __name__ == "__main__":
    worker = RetrainingWorker()
    worker.retrain_models()
