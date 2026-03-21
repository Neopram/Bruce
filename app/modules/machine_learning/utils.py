import numpy as np
from sklearn.preprocessing import MinMaxScaler

def preprocess(data):
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)
    return scaled_data

def save_to_npy(data, path):
    np.save(path, data)
