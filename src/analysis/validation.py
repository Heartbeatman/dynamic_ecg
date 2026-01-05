"""Validation metrics for R peak detection algorithms."""
import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Results from peak detection validation."""
    true_positives: int
    false_positives: int
    false_negatives: int
    sensitivity: float
    positive_predictivity: float
    f1_score: float
    detection_error_rate: float

    def __str__(self) -> str:
        return (
            f"TP: {self.true_positives}, FP: {self.false_positives}, FN: {self.false_negatives}\n"
            f"Sensitivity: {self.sensitivity:.4f} ({self.sensitivity*100:.2f}%)\n"
            f"Positive Predictivity: {self.positive_predictivity:.4f} ({self.positive_predictivity*100:.2f}%)\n"
            f"F1 Score: {self.f1_score:.4f}\n"
            f"Detection Error Rate: {self.detection_error_rate:.4f}%"
        )


def match_peaks(
    detected: np.ndarray,
    ground_truth: np.ndarray,
    tolerance_samples: int
) -> Tuple[int, int, int]:
    """
    Match detected peaks to ground truth annotations.

    Uses a greedy matching algorithm where each ground truth peak
    is matched to the closest detected peak within the tolerance window.
    Each detected peak can only be matched once.

    Args:
        detected: Array of detected peak sample indices
        ground_truth: Array of ground truth peak sample indices
        tolerance_samples: Maximum distance (in samples) for a match

    Returns:
        Tuple of (true_positives, false_positives, false_negatives)
    """
    if len(detected) == 0:
        return 0, 0, len(ground_truth)

    if len(ground_truth) == 0:
        return 0, len(detected), 0

    # Track which detected peaks have been matched
    matched_detected = set()
    true_positives = 0

    # For each ground truth peak, find the closest unmatched detected peak
    for gt_peak in ground_truth:
        # Calculate distances to all detected peaks
        distances = np.abs(detected - gt_peak)

        # Find peaks within tolerance
        within_tolerance = np.where(distances <= tolerance_samples)[0]

        # Filter out already matched peaks
        available = [i for i in within_tolerance if i not in matched_detected]

        if available:
            # Match to the closest available peak
            closest_idx = available[np.argmin(distances[available])]
            matched_detected.add(closest_idx)
            true_positives += 1

    false_positives = len(detected) - len(matched_detected)
    false_negatives = len(ground_truth) - true_positives

    return true_positives, false_positives, false_negatives


def calculate_metrics(
    detected: np.ndarray,
    ground_truth: np.ndarray,
    fs: int,
    tolerance_ms: float = 150.0
) -> ValidationResult:
    """
    Calculate validation metrics for peak detection.

    Args:
        detected: Array of detected peak sample indices (or Nx2 array with indices in column 0)
        ground_truth: Array of ground truth peak sample indices
        fs: Sampling frequency in Hz
        tolerance_ms: Tolerance window in milliseconds (default 150ms per ANSI/AAMI standard)

    Returns:
        ValidationResult with all metrics
    """
    # Handle Nx2 array format (index, width)
    if detected.ndim == 2:
        detected = detected[:, 0]

    # Convert tolerance from ms to samples
    tolerance_samples = int(tolerance_ms * fs / 1000)

    # Match peaks
    tp, fp, fn = match_peaks(detected, ground_truth, tolerance_samples)

    # Calculate metrics
    # Sensitivity (Se) = TP / (TP + FN) - how many true beats were detected
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    # Positive Predictivity (+P) = TP / (TP + FP) - how many detections were correct
    positive_predictivity = tp / (tp + fp) if (tp + fp) > 0 else 0.0

    # F1 Score = harmonic mean of Se and +P
    if sensitivity + positive_predictivity > 0:
        f1_score = 2 * sensitivity * positive_predictivity / (sensitivity + positive_predictivity)
    else:
        f1_score = 0.0

    # Detection Error Rate (DER) = (FP + FN) / Total_Beats * 100
    total_beats = len(ground_truth)
    detection_error_rate = ((fp + fn) / total_beats * 100) if total_beats > 0 else 0.0

    return ValidationResult(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        sensitivity=sensitivity,
        positive_predictivity=positive_predictivity,
        f1_score=f1_score,
        detection_error_rate=detection_error_rate
    )


def aggregate_results(results: list) -> Dict[str, float]:
    """
    Aggregate validation results from multiple records.

    Args:
        results: List of ValidationResult objects

    Returns:
        Dictionary with aggregated metrics
    """
    total_tp = sum(r.true_positives for r in results)
    total_fp = sum(r.false_positives for r in results)
    total_fn = sum(r.false_negatives for r in results)

    # Gross metrics (pooled across all records)
    gross_se = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    gross_pp = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    gross_f1 = 2 * gross_se * gross_pp / (gross_se + gross_pp) if (gross_se + gross_pp) > 0 else 0.0

    # Average metrics across records
    avg_se = np.mean([r.sensitivity for r in results])
    avg_pp = np.mean([r.positive_predictivity for r in results])
    avg_f1 = np.mean([r.f1_score for r in results])
    avg_der = np.mean([r.detection_error_rate for r in results])

    return {
        'total_tp': total_tp,
        'total_fp': total_fp,
        'total_fn': total_fn,
        'gross_sensitivity': gross_se,
        'gross_positive_predictivity': gross_pp,
        'gross_f1_score': gross_f1,
        'avg_sensitivity': avg_se,
        'avg_positive_predictivity': avg_pp,
        'avg_f1_score': avg_f1,
        'avg_detection_error_rate': avg_der,
        'num_records': len(results)
    }
