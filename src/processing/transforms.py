"""Signal transformation functions."""
import numpy as np
from scipy import signal as si
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
def grad_square_conv(X: np.ndarray, freq: int = 125, sin_wave: bool = False) -> np.ndarray:
    """
    Transform the signal to find the peaks.

    Args:
        X: The signal
        freq: The frequency of the signal
        sin_wave: Flag to indicate whether to create a sin wave

    Returns:
        The transformed signal
    """
    # Window length is the size of the correlation sliding window
    window_length = int(freq / 5)

    # Create window
    if sin_wave:
        # Create a sin wave
        sliding = np.sin(np.arange(0, np.pi, np.pi / window_length)) ** 2
    else:
        # Create a sliding window of ones
        sliding = np.ones(window_length)

    # Perform differentiation & squaring, as per Pan-Tompkins
    gradient_squared = (np.diff(X)) ** 2
    # Perform the correlation of transformed peak signal with the sliding window
    window = si.correlate(gradient_squared, sliding, mode='same', method='direct')

    return window


def phasor_transform(lead: np.ndarray, rv: float) -> np.ndarray:
    """
    Perform the phasor transform on the lead.
    
    Args:
        lead: The lead to analyse (numpy array)
        rv: The reference scale (float)
        
    Returns:
        The phase of the signal
    """
    phi_t = np.arctan2(lead, rv)
    return phi_t