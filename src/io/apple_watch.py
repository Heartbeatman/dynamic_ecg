"""Apple Watch ECG data processing."""
import pandas as pd
import numpy as np
from typing import Tuple


def csv_to_numpy(file_path: str) -> Tuple[np.ndarray, float]:
    """
    Convert Apple Watch CSV file to numpy array.
    
    Args:
        file_path: Path to the CSV file
    
    Returns:
        x: The ECG signal
        fs: The sampling frequency
    """
    df = pd.read_csv(file_path, sep=',')
    name = df.columns[1]
    # Convert frequency to float
    fs = float(df.iloc[6][name].split(' ')[0])
    
    x = df['Name'][9:-1].astype(np.float64).to_numpy().flatten()
    
    return x, fs