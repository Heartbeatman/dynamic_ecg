"""Numba-optimised functions for peak detection."""
import numpy as np
from numba import jit


@jit(nopython=True, cache=True, fastmath=True)
def classify_peaks_numba(
    peak_indices: np.ndarray,
    widths: np.ndarray,
    amplitudes: np.ndarray,
    valid_indices: np.ndarray,
    spki: float,
    npki: float,
    fs: int,
    refractory_samples: int
) -> tuple:
    """
    Numba-optimised peak classification.

    Args:
        peak_indices: Array of candidate peak indices
        widths: Array of candidate widths
        amplitudes: Array of candidate amplitudes
        valid_indices: Indices that pass initial refractory check
        spki: Initial signal peak estimate
        npki: Initial noise peak estimate
        fs: Sampling frequency
        refractory_samples: Refractory period in samples

    Returns:
        Tuple of (peaks_array, final_spki, final_npki)
    """
    # Pre-allocate output array (max possible size)
    max_peaks = len(valid_indices) * 2  # Account for search-back additions
    refined_peaks = np.empty((max_peaks, 2), dtype=np.float64)
    count = 0

    last_peak_idx = -refractory_samples
    rr_sum = 0.0
    rr_count = 0

    for i in valid_indices:
        peak_idx = peak_indices[i]
        width = widths[i]
        amplitude = amplitudes[i]

        # Re-check refractory against last *accepted* peak
        if peak_idx - last_peak_idx < refractory_samples:
            continue

        # Calculate average RR interval
        avg_rr = rr_sum / rr_count if rr_count > 0 else float(fs)

        # Search-back if RR interval is too long
        rr_interval = peak_idx - last_peak_idx
        threshold = npki + 0.25 * (spki - npki)

        if rr_count > 2 and rr_interval > 1.5 * avg_rr and last_peak_idx >= 0:
            # Search for missed peaks
            search_threshold = 0.5 * threshold
            best_amp = 0.0
            best_idx = -1
            best_width = 0.0

            for j in range(len(peak_indices)):
                if (peak_indices[j] > last_peak_idx + refractory_samples and
                    peak_indices[j] < peak_idx and
                    amplitudes[j] > search_threshold and
                    amplitudes[j] > best_amp):
                    best_amp = amplitudes[j]
                    best_idx = peak_indices[j]
                    best_width = widths[j]

            if best_idx >= 0:
                refined_peaks[count, 0] = best_idx
                refined_peaks[count, 1] = best_width
                count += 1
                spki = 0.125 * best_amp + 0.875 * spki
                rr_sum += best_idx - last_peak_idx
                rr_count += 1
                last_peak_idx = best_idx

        # Recalculate threshold after potential search-back
        threshold = npki + 0.25 * (spki - npki)

        # Classify current peak
        if amplitude > threshold:
            refined_peaks[count, 0] = peak_idx
            refined_peaks[count, 1] = width
            count += 1
            spki = 0.125 * amplitude + 0.875 * spki
            if last_peak_idx >= 0:
                rr_sum += peak_idx - last_peak_idx
                rr_count += 1
            last_peak_idx = peak_idx
        else:
            npki = 0.125 * amplitude + 0.875 * npki

    return refined_peaks[:count], spki, npki


@jit(nopython=True, cache=True, fastmath=True)
def reprocess_training_period(
    peak_indices: np.ndarray,
    widths: np.ndarray,
    amplitudes: np.ndarray,
    spki: float,
    npki: float,
    training_samples: int,
    refractory_samples: int
) -> np.ndarray:
    """
    Reprocess the training period using calibrated thresholds.

    Args:
        peak_indices: Array of candidate peak indices
        widths: Array of candidate widths
        amplitudes: Array of candidate amplitudes
        spki: Calibrated signal peak estimate
        npki: Calibrated noise peak estimate
        training_samples: Number of samples in training period
        refractory_samples: Refractory period in samples

    Returns:
        Array of detected peaks in training period
    """
    threshold = npki + 0.25 * (spki - npki)

    # Pre-allocate output
    max_peaks = 50  # Training period is short, won't have many peaks
    peaks = np.empty((max_peaks, 2), dtype=np.float64)
    count = 0
    last_peak_idx = -refractory_samples

    for i in range(len(peak_indices)):
        peak_idx = peak_indices[i]

        # Only process peaks in training period
        if peak_idx >= training_samples:
            break

        amplitude = amplitudes[i]
        width = widths[i]

        # Check refractory period
        if peak_idx - last_peak_idx < refractory_samples:
            continue

        # Use calibrated threshold
        if amplitude > threshold:
            peaks[count, 0] = peak_idx
            peaks[count, 1] = width
            count += 1
            last_peak_idx = peak_idx

    return peaks[:count]
