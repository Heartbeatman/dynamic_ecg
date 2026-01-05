"""Validate P-wave detection against QT Database ground truth."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import wfdb
from typing import Tuple

from src.processing import filters, transforms

# Path to QT database
QTDB_PATH = 'data/qtdb'


def detect_p_waves_windowed(
    signal: np.ndarray,
    r_peaks: np.ndarray,
    fs: int,
    rv: float = 0.001,
    window_start_ms: float = 250,
    window_end_ms: float = 50
) -> np.ndarray:
    """Detect P waves by searching in a window before each R peak."""
    window_start_samples = int(window_start_ms * fs / 1000)
    window_end_samples = int(window_end_ms * fs / 1000)

    phasor = transforms.phasor_transform(signal, rv=rv)

    p_waves = []
    for r_idx in r_peaks:
        r_sample = int(r_idx)
        search_start = max(0, r_sample - window_start_samples)
        search_end = max(0, r_sample - window_end_samples)

        if search_end <= search_start:
            continue

        window = phasor[search_start:search_end]
        if len(window) == 0:
            continue

        max_idx = np.argmax(window)
        p_sample = search_start + max_idx
        p_waves.append(p_sample)

    return np.array(p_waves)


def load_qtdb_record(record_name: str) -> Tuple[np.ndarray, int, np.ndarray, np.ndarray]:
    """
    Load a QT database record with P wave and R peak annotations.

    Returns:
        Tuple of (signal, fs, p_wave_gt, r_peak_gt)
    """
    record_path = os.path.join(QTDB_PATH, record_name)

    # Read signal
    record = wfdb.rdrecord(record_path)
    signal = record.p_signal[:, 0]  # First channel
    fs = record.fs

    # Read annotations (pu1 = manual annotations)
    try:
        ann = wfdb.rdann(record_path, 'pu1')
    except:
        # Try other annotation extensions
        ann = wfdb.rdann(record_path, 'atr')

    # Extract P wave and R peak locations
    p_waves = []
    r_peaks = []

    for sample, symbol in zip(ann.sample, ann.symbol):
        if symbol == 'p':
            p_waves.append(sample)
        elif symbol == 'N':
            r_peaks.append(sample)

    return signal, fs, np.array(p_waves), np.array(r_peaks)


def calculate_p_wave_metrics(
    detected: np.ndarray,
    ground_truth: np.ndarray,
    fs: int,
    tolerance_ms: float = 75.0
) -> dict:
    """
    Calculate P wave detection metrics.

    Args:
        detected: Detected P wave locations
        ground_truth: Ground truth P wave locations
        fs: Sampling frequency
        tolerance_ms: Tolerance window in milliseconds

    Returns:
        Dictionary with TP, FP, FN, sensitivity, PPV, F1
    """
    tolerance_samples = int(tolerance_ms * fs / 1000)

    matched_gt = set()
    matched_det = set()

    # Match each ground truth to nearest detected within tolerance
    for i, gt in enumerate(ground_truth):
        if len(detected) == 0:
            continue
        distances = np.abs(detected - gt)
        min_idx = np.argmin(distances)
        min_dist = distances[min_idx]

        if min_dist <= tolerance_samples and min_idx not in matched_det:
            matched_gt.add(i)
            matched_det.add(min_idx)

    tp = len(matched_gt)
    fp = len(detected) - len(matched_det)
    fn = len(ground_truth) - len(matched_gt)

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0
    f1 = 2 * sensitivity * ppv / (sensitivity + ppv) if (sensitivity + ppv) > 0 else 0

    return {
        'tp': tp,
        'fp': fp,
        'fn': fn,
        'sensitivity': sensitivity,
        'ppv': ppv,
        'f1': f1
    }


def validate_single_record(record_name: str, verbose: bool = True) -> dict:
    """Validate P wave detection on a single QT database record."""
    # Load record
    signal, fs, p_wave_gt, r_peak_gt = load_qtdb_record(record_name)

    if verbose:
        print(f"\nRecord {record_name}:")
        print(f"  Signal length: {len(signal)} samples ({len(signal)/fs:.1f}s)")
        print(f"  Sample rate: {fs} Hz")
        print(f"  Ground truth - R peaks: {len(r_peak_gt)}, P waves: {len(p_wave_gt)}")

    # Apply highpass filter
    filtered_signal = filters.butter_highpass_filter(signal, fs)

    # Detect P waves using windowed approach with ground truth R peaks
    detected_p = detect_p_waves_windowed(filtered_signal, r_peak_gt, fs, rv=0.001)

    if verbose:
        print(f"  Detected P waves: {len(detected_p)}")

    # Calculate metrics
    metrics = calculate_p_wave_metrics(detected_p, p_wave_gt, fs, tolerance_ms=75.0)

    if verbose:
        print(f"  TP: {metrics['tp']}, FP: {metrics['fp']}, FN: {metrics['fn']}")
        print(f"  Sensitivity: {metrics['sensitivity']*100:.2f}%")
        print(f"  PPV: {metrics['ppv']*100:.2f}%")
        print(f"  F1 Score: {metrics['f1']:.4f}")

    return metrics


def validate_all_records(verbose: bool = True) -> dict:
    """Validate on all available QT database records."""
    # Get list of records
    records = [f.replace('.hea', '') for f in os.listdir(QTDB_PATH) if f.endswith('.hea')]

    if not records:
        print("No QT database records found. Downloading...")
        wfdb.dl_database('qtdb', QTDB_PATH)
        records = [f.replace('.hea', '') for f in os.listdir(QTDB_PATH) if f.endswith('.hea')]

    print(f"Validating P wave detection on {len(records)} QT database records...")
    print("=" * 60)

    all_metrics = []
    total_tp, total_fp, total_fn = 0, 0, 0

    for record in sorted(records):
        try:
            metrics = validate_single_record(record, verbose=verbose)
            all_metrics.append(metrics)
            total_tp += metrics['tp']
            total_fp += metrics['fp']
            total_fn += metrics['fn']
        except Exception as e:
            if verbose:
                print(f"\nRecord {record}: ERROR - {e}")

    # Aggregate results
    print("\n" + "=" * 60)
    print("AGGREGATE RESULTS")
    print("=" * 60)

    gross_se = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    gross_ppv = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    gross_f1 = 2 * gross_se * gross_ppv / (gross_se + gross_ppv) if (gross_se + gross_ppv) > 0 else 0

    print(f"\nTotal TP: {total_tp}, FP: {total_fp}, FN: {total_fn}")
    print(f"Gross Sensitivity: {gross_se*100:.2f}%")
    print(f"Gross PPV: {gross_ppv*100:.2f}%")
    print(f"Gross F1 Score: {gross_f1:.4f}")

    return {
        'total_tp': total_tp,
        'total_fp': total_fp,
        'total_fn': total_fn,
        'gross_sensitivity': gross_se,
        'gross_ppv': gross_ppv,
        'gross_f1': gross_f1
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Validate P wave detection against QT Database')
    parser.add_argument('--record', '-r', type=str, help='Single record to validate')
    parser.add_argument('--all', '-a', action='store_true', help='Validate all records')
    parser.add_argument('--download', '-d', action='store_true', help='Download QT database first')
    args = parser.parse_args()

    if args.download:
        print("Downloading QT Database...")
        wfdb.dl_database('qtdb', QTDB_PATH)

    if args.record:
        validate_single_record(args.record)
    elif args.all:
        validate_all_records()
    else:
        # Default: validate single record
        validate_single_record('sel100')
