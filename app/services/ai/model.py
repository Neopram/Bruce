
import numpy as np
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler

class PredictiveAI:
    def __init__(self):
        self.model = load_model("models/lstm_model.h5")
        self.scaler = MinMaxScaler()

    def predict(self, data=None):
        if data is None:
            data = np.random.rand(10, 1)
        data_scaled = self.scaler.fit_transform(data)
        prediction = self.model.predict(data_scaled.reshape(1, -1))
        return float(prediction[0][0])
