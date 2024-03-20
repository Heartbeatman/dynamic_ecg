import numpy as np
from scipy import signal as si
from scipy.signal import butter,filtfilt




def butter_highpass_filter(signal, fs):
    """
    Function to filter the signal. 
    Gets rid of baseline wander.
    args:
        signal: the signal to filter
    """
    # Filter requirements.
    nyq = 0.5 * fs
    cutoff = 0.8
    order = 2
    # Get the filter coefficients 
    b, a = butter(order, cutoff/nyq, btype='high', analog=False)
    y = filtfilt(b, a, signal)
    return y

def standardise(X):
    """
    Function to scale the signal to zero mean and unit variance.
    args:
        X: the signal to scale
    """
    mean = np.mean(X, axis=0)
    std_dev = np.std(X, axis=0)
    return (X - mean) / std_dev
