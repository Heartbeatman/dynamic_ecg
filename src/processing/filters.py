"""Signal filtering functions."""
import numpy as np
from scipy.signal import butter, filtfilt


def butter_highpass_filter(signal, fs):
    """
    Filter the signal to remove baseline wander.
    
    Args:
        signal: The signal to filter
        fs: Sampling frequency
        
    Returns:
        Filtered signal
    """
    # Filter requirements
    nyq = 0.5 * fs
    cutoff = 0.8
    order = 2
    # Get the filter coefficients 
    b, a = butter(order, cutoff/nyq, btype='high', analog=False)
    y = filtfilt(b, a, signal)
    return y


def standardise(X):
    """
    Scale the signal to zero mean and unit variance.
    
    Args:
        X: The signal to scale
        
    Returns:
        Standardised signal
    """
    mean = np.mean(X, axis=0)
    std_dev = np.std(X, axis=0)
    return (X - mean) / std_dev