"""Wave detection algorithms."""
import numpy as np
import time
from typing import Callable, Any


def timer_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to time function execution."""
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time for {func.__name__}: {execution_time} seconds")
        return result
    return wrapper


@timer_decorator
def peak(signal: np.ndarray, threshold: float) -> np.ndarray:
    """
    Find the peaks of a signal.
    
    Args:
        signal: The signal
        threshold: The threshold
        
    Returns:
        The peaks of the signal
    """
    # Calibrate the signal by pinning a 1 to the start and end of the signal
    signal = np.concatenate((np.ones(1), signal, np.ones(1)))
    T = np.flatnonzero(signal > threshold)
    dT = np.diff(T) - 1
    edges = np.flatnonzero(dT) + 1
    W = np.column_stack((edges[:-1], edges[1:]))
    WE = np.rint(0.5 * (W[:, 0] + W[:, 1])).astype(int)
    F_in = np.column_stack((T[WE], (np.diff(W)[:, 0])))

    return F_in


def filter_by_width(beat_array: np.ndarray, lower: float, upper: float) -> np.ndarray:
    """
    Filter beats by width.
    
    Args:
        beat_array: numpy array of beats
        lower: lower bound for size
        upper: upper bound for size
        
    Returns:
        numpy array of beats filtered by size
    """
    beat_array = beat_array[(beat_array[:, 1] > lower) & (beat_array[:, 1] < upper)]
    return beat_array