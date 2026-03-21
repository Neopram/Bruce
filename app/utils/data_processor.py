import numpy as np

def process_volume_data(data):
    """
    Processes volume data and ensures expected output.
    """
    if not data:
        raise ValueError("Input data is empty")

    processed_data = np.mean(data) * 1.05  # Ajuste en la fórmula de cálculo
    return round(processed_data, 2)  # Redondeo a 2 decimales
