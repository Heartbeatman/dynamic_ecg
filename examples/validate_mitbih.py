"""Validate R peak detection against MIT-BIH Arrhythmia Database."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.analysis.validation import (
    ValidationResult,
    aggregate_results,
    calculate_metrics,
)
from src.io.mitbih import get_record_info, list_mitbih_records, load_mitbih_record
from src.processing import filters

# Path to MIT-BIH database
DATABASE_PATH = "data/mit-bih-arrhythmia-database-1.0-2.0"


def validate_single_record(record_name: str, verbose: bool = True) -> ValidationResult:
    """
    Validate R peak detection on a single MIT-BIH record.

    Args:
        record_name: Name of the record (e.g., '100')
        verbose: Print detailed results

    Returns:
        ValidationResult object
    """
    record_path = os.path.join(DATABASE_PATH, record_name)

    # Load record and ground truth
    lead, ground_truth = load_mitbih_record(record_path, channel=0)

    # Apply highpass filter to remove baseline wander (skip /1000 scaling - MIT-BIH is already in mV)
    lead.signal = filters.butter_highpass_filter(lead.signal, lead.fs)

    # Run R peak detection
    lead.r_wave_detector(adaptive=True)

    # Calculate metrics
    result = calculate_metrics(
        detected=lead.r_peaks, ground_truth=ground_truth, fs=lead.fs, tolerance_ms=150.0
    )

    if verbose:
        info = get_record_info(record_path)
        print(f"\nRecord {record_name} ({info['sig_name'][0]}):")
        print(
            f"  Duration: {info['duration_minutes']:.1f} min, Ground truth beats: {len(ground_truth)}"
        )
        print(
            f"  Detected: {len(lead.r_peaks)}, TP: {result.true_positives}, FP: {result.false_positives}, FN: {result.false_negatives}"
        )
        print(
            f"  Se: {result.sensitivity * 100:.2f}%, +P: {result.positive_predictivity * 100:.2f}%, F1: {result.f1_score:.4f}"
        )

    return result


def validate_all_records(verbose: bool = True) -> dict:
    """
    Validate R peak detection on all MIT-BIH records.

    Args:
        verbose: Print per-record results

    Returns:
        Dictionary with aggregated results
    """
    records = list_mitbih_records(DATABASE_PATH)
    results = []

    print(f"Validating {len(records)} MIT-BIH records...")
    print("=" * 60)

    for record_name in records:
        try:
            result = validate_single_record(record_name, verbose=verbose)
            results.append(result)
        except Exception as e:
            print(f"\nRecord {record_name}: ERROR - {e}")

    print("\n" + "=" * 60)
    print("AGGREGATE RESULTS")
    print("=" * 60)

    agg = aggregate_results(results)

    print(f"\nTotal records: {agg['num_records']}")
    print(f"Total TP: {agg['total_tp']}, FP: {agg['total_fp']}, FN: {agg['total_fn']}")
    print(f"\nGross Sensitivity: {agg['gross_sensitivity'] * 100:.2f}%")
    print(
        f"Gross Positive Predictivity: {agg['gross_positive_predictivity'] * 100:.2f}%"
    )
    print(f"Gross F1 Score: {agg['gross_f1_score']:.4f}")
    print(f"\nAverage Sensitivity: {agg['avg_sensitivity'] * 100:.2f}%")
    print(
        f"Average Positive Predictivity: {agg['avg_positive_predictivity'] * 100:.2f}%"
    )
    print(f"Average F1 Score: {agg['avg_f1_score']:.4f}")
    print(f"Average Detection Error Rate: {agg['avg_detection_error_rate']:.2f}%")

    return agg


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate R peak detection against MIT-BIH"
    )
    parser.add_argument(
        "--record", "-r", type=str, help="Single record to validate (e.g., 100)"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress per-record output"
    )
    args = parser.parse_args()

    if args.record:
        result = validate_single_record(args.record, verbose=True)
        print(f"\n{result}")
    else:
        validate_all_records(verbose=not args.quiet)
