"""ECG metrics and statistics calculations."""
import numpy as np


def calculate_hrv_metrics(rr_intervals):
    """
    Calculate heart rate variability metrics.
    
    Args:
        rr_intervals: Array of RR intervals
        
    Returns:
        Dictionary of HRV metrics
    """
    metrics = {}
    
    # Time domain metrics
    metrics['mean_rr'] = np.mean(rr_intervals)
    metrics['sdnn'] = np.std(rr_intervals)
    metrics['rmssd'] = np.sqrt(np.mean(np.diff(rr_intervals) ** 2))
    
    # pNN50: percentage of successive differences > 50ms
    successive_diff = np.abs(np.diff(rr_intervals))
    metrics['pnn50'] = (np.sum(successive_diff > 50) / len(successive_diff)) * 100
    
    return metrics