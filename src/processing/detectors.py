"""Wave detection algorithms."""
import numpy as np
import time
from typing import Callable, Any, Tuple, List

from .optimised import classify_peaks_numba, reprocess_training_period


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



def peak_core(signal: np.ndarray, threshold: float) -> np.ndarray:
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
    return peak_core(signal, threshold)


# --- Adaptive Peak Detection Components ---

def calculate_adaptive_threshold(spki: float, npki: float) -> float:
    """Calculate adaptive threshold from signal and noise peak estimates."""
    return npki + 0.25 * (spki - npki)


def update_signal_peak_estimate(spki: float, amplitude: float) -> float:
    """Update signal peak estimate after detecting an R wave."""
    return 0.125 * amplitude + 0.875 * spki


def update_noise_peak_estimate(npki: float, amplitude: float) -> float:
    """Update noise peak estimate."""
    return 0.125 * amplitude + 0.875 * npki


def init_thresholds_from_training(
    signal: np.ndarray,
    fs: int,
    training_duration: float = 2.0
) -> Tuple[float, float]:
    """
    Initialise SPKI and NPKI from a training segment.

    Uses the first few seconds of signal to estimate initial threshold levels
    by finding peaks and classifying them as signal or noise based on amplitude.

    Args:
        signal: The transformed signal
        fs: Sampling frequency
        training_duration: Duration of training segment in seconds

    Returns:
        Tuple of (spki, npki) initial estimates
    """
    training_samples = int(training_duration * fs)
    training_signal = signal[:training_samples]

    # Find candidate peaks with low threshold (max/8)
    training_threshold = np.max(training_signal) / 8
    training_peaks = peak_core(training_signal, training_threshold)

    # Fallback if no peaks found
    if len(training_peaks) == 0:
        training_threshold = np.percentile(signal, 95)
        training_peaks = peak_core(training_signal, training_threshold)

    if len(training_peaks) > 0:
        amplitudes = signal[training_peaks[:, 0].astype(int)]
        sorted_amps = np.sort(amplitudes)[::-1]

        # Top 30% are likely signal peaks, rest are noise
        n_signal = max(1, int(len(sorted_amps) * 0.3))
        spki = np.mean(sorted_amps[:n_signal])
        npki = np.mean(sorted_amps[n_signal:]) if len(sorted_amps) > n_signal else spki / 4
    else:
        spki = np.max(signal) / 4
        npki = np.mean(signal)

    return spki, npki


def get_candidate_peaks(signal: np.ndarray, percentile: float = 60.0) -> np.ndarray:
    """
    Get all candidate peaks using a low threshold.

    Uses a percentile-based threshold to capture all possible peaks.
    Filtering happens later in the adaptive classification phase.

    Args:
        signal: The transformed signal
        percentile: Percentile for threshold calculation

    Returns:
        Array of candidate peaks with columns [peak_index, wave_width]
    """
    candidate_threshold = np.percentile(signal, percentile)
    return peak_core(signal, candidate_threshold)


def search_back_for_missed_peak(
    signal: np.ndarray,
    candidates: np.ndarray,
    search_start: int,
    search_end: int,
    threshold: float
) -> Tuple[int, int, float] | None:
    """
    Search for a missed peak in a region where RR interval was too long.

    Args:
        signal: The transformed signal
        candidates: Array of all candidate peaks
        search_start: Start index for search region
        search_end: End index for search region
        threshold: Lower threshold for search-back (typically 0.5 * normal threshold)

    Returns:
        Tuple of (peak_index, width, amplitude) if found, None otherwise
    """
    missed_candidates = [
        (int(p), w) for p, w in candidates
        if search_start < int(p) < search_end and signal[int(p)] > threshold
    ]

    if not missed_candidates:
        return None

    # Return the highest amplitude peak
    best = max(missed_candidates, key=lambda x: signal[x[0]])
    return (best[0], best[1], signal[best[0]])


def classify_peaks(
    signal: np.ndarray,
    candidates: np.ndarray,
    spki: float,
    npki: float,
    fs: int
) -> Tuple[np.ndarray, float, float]:
    """
    Classify candidate peaks as signal or noise using adaptive thresholding.

    Args:
        signal: The transformed signal
        candidates: Array of candidate peaks
        spki: Initial signal peak estimate
        npki: Initial noise peak estimate
        fs: Sampling frequency

    Returns:
        Tuple of (peaks_array, final_spki, final_npki)
    """
    refractory_samples = int(0.15 * fs)

    # Pre-compute all values using NumPy
    peak_indices = candidates[:, 0].astype(np.int64)
    widths = candidates[:, 1].astype(np.float64)
    amplitudes = signal[peak_indices]

    # Pre-compute intervals between consecutive candidates
    intervals = np.diff(peak_indices, prepend=-refractory_samples)

    # Find candidates that pass refractory check
    refractory_mask = intervals >= refractory_samples
    valid_indices = np.where(refractory_mask)[0].astype(np.int64)

    # Call numba-optimised function
    return classify_peaks_numba(
        peak_indices, widths, amplitudes, valid_indices,
        spki, npki, fs, refractory_samples
    )


@timer_decorator
def adaptive_peak_detect(signal: np.ndarray, fs: int) -> np.ndarray:
    """
    Pan-Tompkins adaptive threshold peak detection with two-pass approach.

    Uses a training phase to learn initial thresholds, then applies adaptive
    thresholding. After the first pass, reprocesses the training period using
    calibrated thresholds to catch initially missed beats.

    Args:
        signal: Transformed signal (after bandpass, derivative, squaring, integration)
        fs: Sampling frequency

    Returns:
        Array with columns [peak_index, wave_width]
    """
    # Initialise thresholds from training phase
    spki, npki = init_thresholds_from_training(signal, fs)
    training_samples = int(2 * fs)
    refractory_samples = int(0.15 * fs)

    # Get all candidate peaks
    candidates = get_candidate_peaks(signal)
    if len(candidates) == 0:
        return np.array([]).reshape(0, 2)

    # First pass: classify peaks using adaptive thresholding
    refined_peaks, final_spki, final_npki = classify_peaks(signal, candidates, spki, npki, fs)

    if len(refined_peaks) == 0:
        return np.array([]).reshape(0, 2)

    # Second pass: reprocess training period with calibrated thresholds
    peak_indices = candidates[:, 0].astype(np.int64)
    widths = candidates[:, 1].astype(np.float64)
    amplitudes = signal[peak_indices]

    training_peaks = reprocess_training_period(
        peak_indices, widths, amplitudes,
        final_spki, final_npki,
        training_samples, refractory_samples
    )

    # Merge results: combine training peaks with main peaks (excluding duplicates)
    if len(training_peaks) > 0:
        # Remove any peaks from refined_peaks that are in training period
        # (they will be replaced by the reprocessed ones)
        main_peaks = refined_peaks[refined_peaks[:, 0] >= training_samples]
        all_peaks = np.vstack([training_peaks, main_peaks]) if len(main_peaks) > 0 else training_peaks
    else:
        all_peaks = refined_peaks

    # Sort peaks by index
    sorted_indices = np.argsort(all_peaks[:, 0])
    all_peaks = all_peaks[sorted_indices]

    return all_peaks


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