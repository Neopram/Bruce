import logging
import numpy as np
import pandas as pd
import asyncio
import aiohttp
import tensorflow as tf
import shap
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, MultiHeadAttention, LayerNormalization, Flatten
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import KFold
from app.config.settings import Config

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Check for GPU availability and enable CUDA acceleration
if tf.config.list_physical_devices('GPU'):
    logging.info("⚡ GPU acceleration is enabled for TensorFlow!")
    tf.config.experimental.set_memory_growth(tf.config.list_physical_devices('GPU')[0], True)
else:
    logging.warning("🚨 Running on CPU. Performance may be limited.")

# Constants
MAX_RETRIES = 3
LSTM_UNITS = 128
DROPOUT_RATE = 0.3
USE_TRANSFORMER = True  # Toggle between LSTM and Transformer models

class PredictiveModel:
    """
    AI-powered market prediction model using LSTMs, Transformers, and SHAP Explainability.
    Supports real-time learning and cross-validation.
    """

    def __init__(self, model_file="lstm_model.h5", lookback=10):
        """
        Initializes the predictive model and attempts to load a pre-trained model.
        """
        self.model_file = model_file
        self.lookback = lookback
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.load_model()

    def load_model(self):
        """
        Loads a pre-trained model if available.
        """
        try:
            self.model = load_model(self.model_file)
            logging.info("✅ Model loaded successfully.")
        except:
            logging.warning("⚠️ No pre-trained model found. A new model will be trained.")

    async def save_model(self):
        """
        Saves the trained model asynchronously.
        """
        if self.model:
            await asyncio.to_thread(self.model.save, self.model_file)
            logging.info("📁 Model saved successfully.")

    def prepare_data(self, data):
        """
        Prepares data for training.
        """
        if "price" not in data.columns:
            raise ValueError("❌ Data must contain a 'price' column.")

        prices = data["price"].values.reshape(-1, 1)
        scaled_prices = self.scaler.fit_transform(prices)

        X, y = [], []
        for i in range(self.lookback, len(scaled_prices)):
            X.append(scaled_prices[i - self.lookback:i, 0])
            y.append(scaled_prices[i, 0])

        return np.array(X).reshape(-1, self.lookback, 1), np.array(y)

    def build_lstm_model(self, input_shape):
        """
        Builds an LSTM-based predictive model.
        """
        model = Sequential([
            LSTM(LSTM_UNITS, return_sequences=True, input_shape=input_shape),
            Dropout(DROPOUT_RATE),
            LSTM(LSTM_UNITS // 2, return_sequences=False),
            Dropout(DROPOUT_RATE / 2),
            Dense(64, activation="relu"),
            Dense(1)
        ])
        model.compile(optimizer="adam", loss="mean_squared_error")
        return model

    def build_transformer_model(self, input_shape):
        """
        Builds a Transformer-based predictive model.
        """
        inputs = tf.keras.Input(shape=input_shape)
        x = MultiHeadAttention(num_heads=4, key_dim=16)(inputs, inputs)
        x = LayerNormalization(epsilon=1e-6)(x)
        x = Flatten()(x)
        x = Dense(64, activation="relu")(x)
        outputs = Dense(1)(x)

        model = tf.keras.Model(inputs, outputs)
        model.compile(optimizer="adam", loss="mean_squared_error")
        return model

    async def train(self, historical_data, epochs=100, batch_size=64):
        """
        Trains the model asynchronously with K-Fold Cross Validation.
        """
        X, y = self.prepare_data(historical_data)

        kf = KFold(n_splits=5, shuffle=True)
        best_model = None
        best_loss = float("inf")

        for train_idx, val_idx in kf.split(X):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            self.model = self.build_transformer_model((X_train.shape[1], 1)) if USE_TRANSFORMER else self.build_lstm_model((X_train.shape[1], 1))

            early_stopping = EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)
            history = await asyncio.to_thread(self.model.fit, X_train, y_train, validation_data=(X_val, y_val),
                                              epochs=epochs, batch_size=batch_size, callbacks=[early_stopping])

            val_loss = min(history.history["val_loss"])
            if val_loss < best_loss:
                best_loss = val_loss
                best_model = self.model

        self.model = best_model
        await self.save_model()

    async def predict(self, recent_data):
        """
        Generates a price prediction asynchronously.
        """
        if self.model is None:
            raise ValueError("❌ Model is not trained. Train the model first.")

        scaled_data = self.scaler.transform(np.array(recent_data).reshape(-1, 1))
        input_data = scaled_data[-self.lookback:].reshape(1, self.lookback, 1)
        scaled_prediction = await asyncio.to_thread(self.model.predict, input_data)
        return self.scaler.inverse_transform([[scaled_prediction[0][0]]])[0][0]

    async def enhanced_prediction(self, recent_prices):
        """
        Adjusts predictions based on SHAP Explainability and market conditions.
        """
        base_prediction = await self.predict(recent_prices)

        # SHAP Analysis
        explainer = shap.Explainer(self.model, np.array(recent_prices).reshape(-1, 1))
        shap_values = explainer.shap_values(np.array(recent_prices).reshape(-1, 1))
        influence_factor = np.mean(shap_values)
        adjusted_prediction = base_prediction * (1 + influence_factor)

        logging.info(f"🔮 Prediction: {adjusted_prediction} (SHAP Influence: {influence_factor})")
        return adjusted_prediction

# Example Usage
if __name__ == "__main__":
    model = PredictiveModel()
    recent_prices = [45000, 45200, 45350, 45500, 45750]
    predicted_price = asyncio.run(model.enhanced_prediction(recent_prices))
    logging.info(f"📊 Final predicted price: {predicted_price}")
