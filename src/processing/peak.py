"""Simple threshold-based peak detection algorithms."""
import numpy as np

from .utils import timer_decorator


def peak_core(signal: np.ndarray, threshold: float) -> np.ndarray:
    """
    Core peak detection logic.

    Finds peaks by identifying contiguous regions above threshold
    and returning their midpoints with widths.

    Args:
        signal: The signal to search for peaks
        threshold: Amplitude threshold for peak detection

    Returns:
        Array with columns [peak_index, wave_width]
    """
    # Pad the signal with ones on both sides to handle edge cases!
    padded_signal = np.concatenate((np.ones(1), signal, np.ones(1)))

    # Find indexes where signal is greater than threshold
    points = np.flatnonzero(padded_signal > threshold)

    if len(points) < 2:
        return np.array([]).reshape(0, 2)

    # Find the difference between consecutive points minus 1
    # Large values indicate edges between separate peaks :)
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
    Find the peaks of a signal using fixed threshold.

    Simple wrapper around peak_core with timing information.

    Args:
        signal: The signal to search for peaks
        threshold: Amplitude threshold for peak detection

    Returns:
        Array with columns [peak_index, wave_width]
    """
    return peak_core(signal, threshold)


def filter_by_width(beat_array: np.ndarray, lower: float, upper: float) -> np.ndarray:
    """
    Filter beats by width.

    Useful for removing artifacts or non-QRS peaks based on their duration.

    Args:
        beat_array: numpy array of beats with columns [index, width]
        lower: lower bound for width (exclusive)
        upper: upper bound for width (exclusive)

    Returns:
        numpy array of beats filtered by width
    """
    beat_array = beat_array[(beat_array[:, 1] > lower) & (beat_array[:, 1] < upper)]
    return beat_array
