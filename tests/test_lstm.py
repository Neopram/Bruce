
# tests/test_lstm.py
import os

def test_lstm_model_loaded():
    assert os.path.exists("lstm_model.h5"), "LSTM model no encontrado"
