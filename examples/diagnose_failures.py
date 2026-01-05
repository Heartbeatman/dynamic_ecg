"""Diagnose where R peak detection failed on MIT-BIH records."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple
from dataclasses import dataclass

from src.io.mitbih import load_mitbih_record, get_record_info
from src.processing import filters


# Path to MIT-BIH database
DATABASE_PATH = 'data/mit-bih-arrhythmia-database-1.0-2.0'


@dataclass
class FailureInfo:
    """Information about a detection failure."""
    sample_idx: int
    time_seconds: float
    amplitude: float
    failure_type: str  # 'FN' (false negative) or 'FP' (false positive)
    nearest_match_distance: int  # Distance to nearest detected/ground truth peak


def match_peaks(
    detected: np.ndarray,
    ground_truth: np.ndarray,
    tolerance_samples: int
) -> Tuple[List[int], List[int], List[int]]:
    """
    Match detected peaks to ground truth within tolerance.

    Returns:
        Tuple of (matched_gt_indices, fn_indices, fp_indices)
    """
    detected_indices = detected[:, 0].astype(int) if len(detected) > 0 else np.array([])
    gt_indices = ground_truth.astype(int)

    matched_gt = set()
    matched_det = set()

    # Match each ground truth to nearest detected peak within tolerance
    for i, gt_idx in enumerate(gt_indices):
        if len(detected_indices) == 0:
            continue
        distances = np.abs(detected_indices - gt_idx)
        min_dist_idx = np.argmin(distances)
        min_dist = distances[min_dist_idx]

        if min_dist <= tolerance_samples and min_dist_idx not in matched_det:
            matched_gt.add(i)
            matched_det.add(min_dist_idx)

    # False negatives: ground truth peaks not matched
    fn_indices = [i for i in range(len(gt_indices)) if i not in matched_gt]

    # False positives: detected peaks not matched
    fp_indices = [i for i in range(len(detected_indices)) if i not in matched_det]

    return list(matched_gt), fn_indices, fp_indices


def find_nearest_distance(target_idx: int, reference_indices: np.ndarray) -> int:
    """Find distance to nearest index in reference array."""
    if len(reference_indices) == 0:
        return -1
    distances = np.abs(reference_indices - target_idx)
    return int(np.min(distances))


def diagnose_record(
    record_name: str,
    tolerance_ms: float = 150.0,
    show_fn: bool = True,
    show_fp: bool = True,
    limit: int = None
) -> Tuple[List[FailureInfo], List[FailureInfo]]:
    """
    Diagnose detection failures on a single MIT-BIH record.

    Args:
        record_name: Name of the record (e.g., '100')
        tolerance_ms: Tolerance window in milliseconds
        show_fn: Show false negatives
        show_fp: Show false positives
        limit: Limit number of failures to show (None for all)

    Returns:
        Tuple of (false_negatives, false_positives) as FailureInfo lists
    """
    record_path = os.path.join(DATABASE_PATH, record_name)

    # Load record and ground truth
    lead, ground_truth = load_mitbih_record(record_path, channel=0)
    fs = lead.fs
    tolerance_samples = int(tolerance_ms * fs / 1000)

    # Store raw signal for amplitude lookup
    raw_signal = lead.signal.copy()

    # Apply highpass filter
    lead.signal = filters.butter_highpass_filter(lead.signal, fs)

    # Run R peak detection
    lead.r_wave_detector(adaptive=True)
    detected = lead.r_peaks

    # Get record info
    info = get_record_info(record_path)

    print(f"\n{'='*70}")
    print(f"DIAGNOSIS: Record {record_name} ({info['sig_name'][0]})")
    print(f"{'='*70}")
    print(f"Duration: {info['duration_minutes']:.1f} min | Sample rate: {fs} Hz")
    print(f"Ground truth beats: {len(ground_truth)} | Detected beats: {len(detected)}")
    print(f"Tolerance: {tolerance_ms}ms ({tolerance_samples} samples)")

    # Match peaks
    _, fn_indices, fp_indices = match_peaks(detected, ground_truth, tolerance_samples)

    print(f"\nFalse Negatives (missed beats): {len(fn_indices)}")
    print(f"False Positives (extra detections): {len(fp_indices)}")

    false_negatives = []
    false_positives = []

    detected_indices = detected[:, 0].astype(int) if len(detected) > 0 else np.array([])
    gt_indices = ground_truth.astype(int)

    # Analyse false negatives
    if show_fn and len(fn_indices) > 0:
        print(f"\n{'-'*70}")
        print("FALSE NEGATIVES (missed ground truth beats)")
        print(f"{'-'*70}")
        print(f"{'Sample':>10} | {'Time (s)':>10} | {'Amplitude':>12} | {'Nearest Det':>12}")
        print(f"{'-'*10}-+-{'-'*10}-+-{'-'*12}-+-{'-'*12}")

        display_count = min(len(fn_indices), limit) if limit else len(fn_indices)

        for i in range(display_count):
            gt_idx = gt_indices[fn_indices[i]]
            time_sec = gt_idx / fs
            amplitude = raw_signal[gt_idx]
            nearest_dist = find_nearest_distance(gt_idx, detected_indices)

            failure = FailureInfo(
                sample_idx=int(gt_idx),
                time_seconds=time_sec,
                amplitude=float(amplitude),
                failure_type='FN',
                nearest_match_distance=nearest_dist
            )
            false_negatives.append(failure)

            nearest_str = f"{nearest_dist} samples" if nearest_dist >= 0 else "N/A"
            print(f"{gt_idx:>10} | {time_sec:>10.3f} | {amplitude:>12.4f} | {nearest_str:>12}")

        if limit and len(fn_indices) > limit:
            print(f"... and {len(fn_indices) - limit} more")

    # Analyse false positives
    if show_fp and len(fp_indices) > 0:
        print(f"\n{'-'*70}")
        print("FALSE POSITIVES (extra detections not in ground truth)")
        print(f"{'-'*70}")
        print(f"{'Sample':>10} | {'Time (s)':>10} | {'Amplitude':>12} | {'Nearest GT':>12}")
        print(f"{'-'*10}-+-{'-'*10}-+-{'-'*12}-+-{'-'*12}")

        display_count = min(len(fp_indices), limit) if limit else len(fp_indices)

        for i in range(display_count):
            det_idx = detected_indices[fp_indices[i]]
            time_sec = det_idx / fs
            amplitude = raw_signal[det_idx]
            nearest_dist = find_nearest_distance(det_idx, gt_indices)

            failure = FailureInfo(
                sample_idx=int(det_idx),
                time_seconds=time_sec,
                amplitude=float(amplitude),
                failure_type='FP',
                nearest_match_distance=nearest_dist
            )
            false_positives.append(failure)

            nearest_str = f"{nearest_dist} samples" if nearest_dist >= 0 else "N/A"
            print(f"{det_idx:>10} | {time_sec:>10.3f} | {amplitude:>12.4f} | {nearest_str:>12}")

        if limit and len(fp_indices) > limit:
            print(f"... and {len(fp_indices) - limit} more")

    # Summary statistics for false negatives
    if len(false_negatives) > 0:
        fn_amplitudes = [f.amplitude for f in false_negatives]
        fn_times = [f.time_seconds for f in false_negatives]
        print(f"\n{'-'*70}")
        print("FALSE NEGATIVE STATISTICS")
        print(f"{'-'*70}")
        print(f"Amplitude - Min: {min(fn_amplitudes):.4f}, Max: {max(fn_amplitudes):.4f}, "
              f"Mean: {np.mean(fn_amplitudes):.4f}, Std: {np.std(fn_amplitudes):.4f}")
        print(f"Time range: {min(fn_times):.2f}s - {max(fn_times):.2f}s")

        # Time distribution
        time_bins = [0, 60, 300, 600, 1200, 1800]
        bin_labels = ['0-1min', '1-5min', '5-10min', '10-20min', '20-30min']
        print("\nTime distribution of missed beats:")
        for i in range(len(time_bins) - 1):
            count = sum(1 for t in fn_times if time_bins[i] <= t < time_bins[i+1])
            if count > 0:
                print(f"  {bin_labels[i]}: {count} beats")

    return false_negatives, false_positives


def diagnose_worst_records(n: int = 5, limit_per_record: int = 20):
    """Diagnose the worst performing records."""
    # Known challenging records from validation
    worst_records = ['228', '114', '215', '203', '208'][:n]

    print("\n" + "="*70)
    print(f"DIAGNOSING {n} WORST PERFORMING RECORDS")
    print("="*70)

    for record in worst_records:
        try:
            diagnose_record(record, limit=limit_per_record)
        except Exception as e:
            print(f"\nRecord {record}: ERROR - {e}")


def plot_failures(
    record_name: str,
    output_dir: str = None,
    window_seconds: float = 3.0,
    tolerance_ms: float = 150.0,
    limit: int = None,
    plot_fn: bool = True,
    plot_fp: bool = True
):
    """
    Generate plots for all detection failures on a record.

    Args:
        record_name: Name of the record (e.g., '228')
        output_dir: Directory to save plots (default: failures_<record>/)
        window_seconds: Time window around each failure to plot
        tolerance_ms: Tolerance window in milliseconds
        limit: Maximum number of plots to generate
        plot_fn: Plot false negatives
        plot_fp: Plot false positives
    """
    record_path = os.path.join(DATABASE_PATH, record_name)

    # Create output directory
    if output_dir is None:
        output_dir = f'failures_{record_name}'
    os.makedirs(output_dir, exist_ok=True)

    # Load record and ground truth
    lead, ground_truth = load_mitbih_record(record_path, channel=0)
    fs = lead.fs
    tolerance_samples = int(tolerance_ms * fs / 1000)
    window_samples = int(window_seconds * fs)

    # Store raw signal for plotting
    raw_signal = lead.signal.copy()

    # Apply highpass filter
    lead.signal = filters.butter_highpass_filter(lead.signal, fs)

    # Run R peak detection
    lead.r_wave_detector(adaptive=True)
    detected = lead.r_peaks

    # Match peaks
    _, fn_indices, fp_indices = match_peaks(detected, ground_truth, tolerance_samples)

    detected_indices = detected[:, 0].astype(int) if len(detected) > 0 else np.array([])
    gt_indices = ground_truth.astype(int)

    print(f"\nGenerating failure plots for record {record_name}...")
    print(f"Output directory: {output_dir}/")
    print(f"False negatives: {len(fn_indices)}, False positives: {len(fp_indices)}")

    plot_count = 0
    total_to_plot = 0

    if plot_fn:
        total_to_plot += len(fn_indices)
    if plot_fp:
        total_to_plot += len(fp_indices)

    if limit:
        total_to_plot = min(total_to_plot, limit)

    # Plot false negatives
    if plot_fn:
        fn_limit = limit if limit else len(fn_indices)
        for i, fn_idx in enumerate(fn_indices[:fn_limit]):
            if limit and plot_count >= limit:
                break

            gt_sample = gt_indices[fn_idx]
            _plot_failure_window(
                raw_signal, fs, gt_sample, window_samples,
                detected_indices, gt_indices, tolerance_samples,
                'FN', record_name, i + 1, output_dir
            )
            plot_count += 1

            if plot_count % 10 == 0:
                print(f"  Generated {plot_count}/{total_to_plot} plots...")

    # Plot false positives
    if plot_fp:
        fp_limit = (limit - plot_count) if limit else len(fp_indices)
        for i, fp_idx in enumerate(fp_indices[:fp_limit]):
            if limit and plot_count >= limit:
                break

            det_sample = detected_indices[fp_idx]
            _plot_failure_window(
                raw_signal, fs, det_sample, window_samples,
                detected_indices, gt_indices, tolerance_samples,
                'FP', record_name, i + 1, output_dir
            )
            plot_count += 1

            if plot_count % 10 == 0:
                print(f"  Generated {plot_count}/{total_to_plot} plots...")

    print(f"Done! Generated {plot_count} plots in {output_dir}/")
    return plot_count


def _plot_failure_window(
    signal: np.ndarray,
    fs: int,
    centre_sample: int,
    window_samples: int,
    detected_indices: np.ndarray,
    gt_indices: np.ndarray,
    tolerance_samples: int,
    failure_type: str,
    record_name: str,
    failure_num: int,
    output_dir: str
):
    """Plot a single failure window."""
    # Calculate window bounds
    half_window = window_samples // 2
    start_sample = max(0, centre_sample - half_window)
    end_sample = min(len(signal), centre_sample + half_window)

    # Extract signal segment
    segment = signal[start_sample:end_sample]
    time_axis = np.arange(start_sample, end_sample) / fs

    # Find peaks in this window
    det_in_window = detected_indices[(detected_indices >= start_sample) & (detected_indices < end_sample)]
    gt_in_window = gt_indices[(gt_indices >= start_sample) & (gt_indices < end_sample)]

    # Create plot
    fig, ax = plt.subplots(figsize=(14, 5))

    # Plot signal
    ax.plot(time_axis, segment, 'b-', linewidth=0.8, label='ECG Signal')

    # Plot ground truth peaks
    for gt in gt_in_window:
        gt_time = gt / fs
        gt_amp = signal[gt]
        # Check if this GT was matched
        matched = any(abs(gt - d) <= tolerance_samples for d in detected_indices)
        if matched:
            ax.axvline(x=gt_time, color='green', alpha=0.3, linestyle='-', linewidth=1)
            ax.plot(gt_time, gt_amp, 'go', markersize=8, label='GT (matched)' if gt == gt_in_window[0] else '')
        else:
            ax.axvline(x=gt_time, color='red', alpha=0.3, linestyle='--', linewidth=2)
            ax.plot(gt_time, gt_amp, 'r^', markersize=12, label='GT (missed)' if gt == gt_in_window[0] else '')

    # Plot detected peaks
    for det in det_in_window:
        det_time = det / fs
        det_amp = signal[det]
        # Check if this detection was matched
        matched = any(abs(det - g) <= tolerance_samples for g in gt_indices)
        if matched:
            ax.plot(det_time, det_amp, 'g*', markersize=10)
        else:
            ax.axvline(x=det_time, color='orange', alpha=0.3, linestyle='--', linewidth=2)
            ax.plot(det_time, det_amp, 'o', color='orange', markersize=12, label='FP Detection')

    # Highlight the centre failure point
    centre_time = centre_sample / fs
    centre_amp = signal[centre_sample]

    if failure_type == 'FN':
        ax.annotate(
            'MISSED',
            xy=(centre_time, centre_amp),
            xytext=(centre_time, centre_amp + 0.3),
            fontsize=12, fontweight='bold', color='red',
            ha='center',
            arrowprops=dict(arrowstyle='->', color='red', lw=2)
        )
        title_color = 'red'
    else:
        ax.annotate(
            'FALSE POSITIVE',
            xy=(centre_time, centre_amp),
            xytext=(centre_time, centre_amp + 0.3),
            fontsize=12, fontweight='bold', color='orange',
            ha='center',
            arrowprops=dict(arrowstyle='->', color='orange', lw=2)
        )
        title_color = 'orange'

    # Title and labels
    ax.set_title(
        f'Record {record_name} - {failure_type} #{failure_num} | '
        f'Sample: {centre_sample} | Time: {centre_time:.2f}s | Amplitude: {centre_amp:.4f}',
        fontsize=12, color=title_color, fontweight='bold'
    )
    ax.set_xlabel('Time (seconds)', fontsize=11)
    ax.set_ylabel('Amplitude (mV)', fontsize=11)
    ax.grid(True, alpha=0.3)

    # Legend (remove duplicates)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right')

    # Save figure
    filename = f'{failure_type}_{failure_num:04d}_sample{centre_sample}.png'
    filepath = os.path.join(output_dir, filename)
    plt.tight_layout()
    plt.savefig(filepath, dpi=100, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Diagnose R peak detection failures')
    parser.add_argument('--record', '-r', type=str, help='Single record to diagnose (e.g., 100)')
    parser.add_argument('--worst', '-w', type=int, default=0,
                        help='Diagnose N worst performing records')
    parser.add_argument('--limit', '-l', type=int, default=50,
                        help='Limit failures shown per record')
    parser.add_argument('--fn-only', action='store_true', help='Show only false negatives')
    parser.add_argument('--fp-only', action='store_true', help='Show only false positives')
    parser.add_argument('--plot', '-p', action='store_true',
                        help='Generate plot images for each failure')
    parser.add_argument('--output-dir', '-o', type=str, default=None,
                        help='Output directory for plots (default: failures_<record>/)')
    parser.add_argument('--window', type=float, default=3.0,
                        help='Window size in seconds for plots (default: 3.0)')
    args = parser.parse_args()

    show_fn = not args.fp_only
    show_fp = not args.fn_only

    if args.record:
        if args.plot:
            plot_failures(
                args.record,
                output_dir=args.output_dir,
                window_seconds=args.window,
                limit=args.limit,
                plot_fn=show_fn,
                plot_fp=show_fp
            )
        else:
            diagnose_record(args.record, show_fn=show_fn, show_fp=show_fp, limit=args.limit)
    elif args.worst > 0:
        diagnose_worst_records(n=args.worst, limit_per_record=args.limit)
    else:
        # Default: diagnose record 228 (worst performer)
        diagnose_record('228', show_fn=show_fn, show_fp=show_fp, limit=args.limit)
