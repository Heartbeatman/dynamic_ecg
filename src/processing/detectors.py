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


def _peak_core(signal: np.ndarray, threshold: float) -> np.ndarray:
    """
    Core peak detection logic.

    Args:
        signal: The signal
        threshold: The threshold

    Returns:
        Array with columns [peak_index, wave_width]
    """
    # Pad the signal with ones on both sides
    padded_signal = np.concatenate((np.ones(1), signal, np.ones(1)))

    # Find indexes where signal is greater than threshold
    points = np.flatnonzero(padded_signal > threshold)

    if len(points) < 2:
        return np.array([]).reshape(0, 2)

    # Find the difference between consecutive points minus 1
    # Large values indicate edges between separate peaks
    diff_points = np.diff(points) - 1

    # Find edge indexes where consecutive points are not adjacent
    edge_index = np.flatnonzero(diff_points) + 1

    if len(edge_index) < 2:
        return np.array([]).reshape(0, 2)

    # Create peak blocks from consecutive edge pairs
    peak_blocks = np.column_stack((edge_index[:-1], edge_index[1:]))

    # Find the midpoint index of each peak block
    peak_midpoint_indexes = np.rint(0.5 * (peak_blocks[:, 0] + peak_blocks[:, 1])).astype(int)

    # Get peak indexes in the time domain with their widths
    peak_index_with_width = np.column_stack((points[peak_midpoint_indexes], np.diff(peak_blocks)[:, 0]))

    return peak_index_with_width


@timer_decorator
def peak(signal: np.ndarray, threshold: float) -> np.ndarray:
    """
    Find the peaks of a signal.

    Args:
        signal: The signal
        threshold: The threshold

    Returns:
        Array with columns [peak_index, wave_width]
    """
    return _peak_core(signal, threshold)


@timer_decorator
def adaptive_peak_detect(signal: np.ndarray, fs: int) -> np.ndarray:
    """
    Pan-Tompkins adaptive threshold peak detection.

    Uses the same peak detection logic as peak() but with adaptive thresholding.
    Dynamically adjusts threshold based on signal and noise peak estimates.

    Args:
        signal: Transformed signal (after bandpass, derivative, squaring, integration)
        fs: Sampling frequency

    Returns:
        Array with columns [peak_index, wave_width]
    """
    # Initialise threshold estimates from signal statistics
    spki = np.max(signal)  # Signal peak estimate
    npki = np.mean(signal)  # Noise peak estimate
    threshold = npki + 0.25 * (spki - npki)

    # Refractory period in samples (200 ms)
    refractory_samples = int(0.2 * fs)

    # First pass: detect peaks with initial threshold using our peak algorithm
    detected = _peak_core(signal, threshold)

    if len(detected) == 0:
        return np.array([]).reshape(0, 2)

    # Adaptive refinement: update threshold based on detected peaks
    refined_peaks = []
    last_peak_idx = -refractory_samples  # Allow first peak

    for peak_idx, width in detected:
        peak_idx = int(peak_idx)
        amplitude = signal[peak_idx]

        # Check refractory period
        if peak_idx - last_peak_idx < refractory_samples:
            continue

        # Adaptive threshold
        threshold = npki + 0.25 * (spki - npki)

        if amplitude > threshold:
            # Signal peak - detected R wave
            refined_peaks.append([peak_idx, width])
            spki = 0.125 * amplitude + 0.875 * spki
            last_peak_idx = peak_idx
        else:
            # Noise peak - update noise estimate
            npki = 0.125 * amplitude + 0.875 * npki

    if len(refined_peaks) == 0:
        return np.array([]).reshape(0, 2)

    return np.array(refined_peaks)


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