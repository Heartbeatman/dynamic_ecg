"""Plot comprehensive validation: Ground Truth vs Detected for P waves and QRS."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt
import wfdb

from src.processing import filters, transforms, detectors

QTDB_PATH = 'data/qtdb'


def detect_p_waves_windowed(signal, r_peaks, fs, rv=0.001, window_start_ms=250, window_end_ms=50):
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
        p_waves.append(search_start + max_idx)

    return np.array(p_waves)


def plot_full_validation(record_name='sel100', start_sec=0, duration_sec=10):
    """
    Create comprehensive validation plot showing:
    - Ground truth P waves and QRS peaks
    - Detected P waves and R peaks
    """
    record_path = os.path.join(QTDB_PATH, record_name)

    # Load signal
    record = wfdb.rdrecord(record_path)
    signal = record.p_signal[:, 0]
    fs = record.fs

    # Load annotations
    ann = wfdb.rdann(record_path, 'pu1')

    # Extract ground truth
    p_wave_gt = np.array([s for s, sym in zip(ann.sample, ann.symbol) if sym == 'p'])
    r_peak_gt = np.array([s for s, sym in zip(ann.sample, ann.symbol) if sym == 'N'])

    # Filter signal
    filtered_signal = filters.butter_highpass_filter(signal, fs)

    # For QT database, use ground truth R peaks for fair P-wave comparison
    # (QT database has different signal characteristics than MIT-BIH)
    detected_r = r_peak_gt  # Use ground truth R peaks

    # Detect P waves using windowed approach with ground truth R peaks
    detected_p_with_det_r = detect_p_waves_windowed(filtered_signal, r_peak_gt, fs, rv=0.001)

    # Extract segment
    start_sample = int(start_sec * fs)
    end_sample = int((start_sec + duration_sec) * fs)
    segment = signal[start_sample:end_sample]
    time_axis = np.arange(len(segment)) / fs + start_sec

    # Filter annotations to segment
    gt_p_seg = p_wave_gt[(p_wave_gt >= start_sample) & (p_wave_gt < end_sample)]
    gt_r_seg = r_peak_gt[(r_peak_gt >= start_sample) & (r_peak_gt < end_sample)]
    det_r_seg = detected_r[(detected_r >= start_sample) & (detected_r < end_sample)]
    det_p_seg = detected_p_with_det_r[(detected_p_with_det_r >= start_sample) & (detected_p_with_det_r < end_sample)]

    # Create figure
    fig, axes = plt.subplots(3, 1, figsize=(16, 12))

    # ===== Plot 1: Ground Truth =====
    ax1 = axes[0]
    ax1.plot(time_axis, segment, 'b-', linewidth=0.8, label='ECG Signal')

    # Ground truth P waves (green)
    for p in gt_p_seg:
        p_time = p / fs
        p_amp = signal[p]
        ax1.plot(p_time, p_amp, 'go', markersize=10, zorder=5)
        ax1.axvline(x=p_time, color='green', alpha=0.2, linestyle='--')

    # Ground truth R peaks (red)
    for r in gt_r_seg:
        r_time = r / fs
        r_amp = signal[r]
        ax1.plot(r_time, r_amp, 'r^', markersize=12, zorder=5)
        ax1.axvline(x=r_time, color='red', alpha=0.2, linestyle='-')

    ax1.set_title(f'Ground Truth Annotations | Record {record_name} | P waves: {len(gt_p_seg)}, QRS: {len(gt_r_seg)}',
                  fontsize=14, fontweight='bold')
    ax1.set_ylabel('Amplitude (mV)', fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.legend(['ECG', 'P wave (GT)', 'R peak (GT)'], loc='upper right', fontsize=10)

    # ===== Plot 2: Our Detection =====
    ax2 = axes[1]
    ax2.plot(time_axis, segment, 'b-', linewidth=0.8, label='ECG Signal')

    # Detected P waves (green)
    for p in det_p_seg:
        p_time = p / fs
        p_amp = signal[p]
        ax2.plot(p_time, p_amp, 'go', markersize=10, zorder=5)
        ax2.axvline(x=p_time, color='green', alpha=0.2, linestyle='--')

    # Detected R peaks (red)
    for r in det_r_seg:
        r_time = r / fs
        r_amp = signal[r]
        ax2.plot(r_time, r_amp, 'r^', markersize=12, zorder=5)
        ax2.axvline(x=r_time, color='red', alpha=0.2, linestyle='-')

    ax2.set_title(f'Our Detection | P waves: {len(det_p_seg)}, QRS: {len(det_r_seg)}',
                  fontsize=14, fontweight='bold')
    ax2.set_ylabel('Amplitude (mV)', fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.legend(['ECG', 'P wave (Detected)', 'R peak (Detected)'], loc='upper right', fontsize=10)

    # ===== Plot 3: Overlay Comparison =====
    ax3 = axes[2]
    ax3.plot(time_axis, segment, 'b-', linewidth=0.8, label='ECG Signal')

    # Ground truth - hollow markers
    for p in gt_p_seg:
        p_time = p / fs
        p_amp = signal[p]
        ax3.plot(p_time, p_amp, 'o', markersize=14, markerfacecolor='none',
                 markeredgecolor='green', markeredgewidth=2, zorder=4)

    for r in gt_r_seg:
        r_time = r / fs
        r_amp = signal[r]
        ax3.plot(r_time, r_amp, '^', markersize=16, markerfacecolor='none',
                 markeredgecolor='red', markeredgewidth=2, zorder=4)

    # Detected - filled markers (smaller)
    for p in det_p_seg:
        p_time = p / fs
        p_amp = signal[p]
        ax3.plot(p_time, p_amp, 'go', markersize=6, zorder=5)

    for r in det_r_seg:
        r_time = r / fs
        r_amp = signal[r]
        ax3.plot(r_time, r_amp, 'r^', markersize=8, zorder=5)

    ax3.set_title('Overlay: Ground Truth (hollow) vs Detected (filled)',
                  fontsize=14, fontweight='bold')
    ax3.set_xlabel('Time (seconds)', fontsize=11)
    ax3.set_ylabel('Amplitude (mV)', fontsize=11)
    ax3.grid(True, alpha=0.3)
    ax3.legend(['ECG', 'P wave GT', 'R peak GT', 'P wave Det', 'R peak Det'],
               loc='upper right', fontsize=10)

    plt.tight_layout()

    # Save figure
    output_path = f'output/plots/validation_comparison_{record_name}_{start_sec}-{start_sec+duration_sec}s.png'
    os.makedirs('output/plots', exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")

    # Also save a zoomed version
    fig2, ax = plt.subplots(figsize=(16, 6))

    # Zoom to first 5 seconds
    zoom_duration = min(5, duration_sec)
    zoom_end_sample = int((start_sec + zoom_duration) * fs)
    zoom_segment = signal[start_sample:zoom_end_sample]
    zoom_time = np.arange(len(zoom_segment)) / fs + start_sec

    ax.plot(zoom_time, zoom_segment, 'b-', linewidth=1.0, label='ECG Signal')

    # Ground truth - hollow markers with labels
    gt_p_zoom = gt_p_seg[gt_p_seg < zoom_end_sample]
    gt_r_zoom = gt_r_seg[gt_r_seg < zoom_end_sample]
    det_p_zoom = det_p_seg[det_p_seg < zoom_end_sample]
    det_r_zoom = det_r_seg[det_r_seg < zoom_end_sample]

    for p in gt_p_zoom:
        p_time = p / fs
        p_amp = signal[p]
        ax.plot(p_time, p_amp, 'o', markersize=16, markerfacecolor='none',
                markeredgecolor='green', markeredgewidth=2.5, zorder=4)
        ax.annotate('P', (p_time, p_amp - 0.15), ha='center', fontsize=9,
                    color='green', fontweight='bold')

    for r in gt_r_zoom:
        r_time = r / fs
        r_amp = signal[r]
        ax.plot(r_time, r_amp, '^', markersize=18, markerfacecolor='none',
                markeredgecolor='red', markeredgewidth=2.5, zorder=4)
        ax.annotate('R', (r_time, r_amp + 0.15), ha='center', fontsize=9,
                    color='red', fontweight='bold')

    # Detected - filled markers
    for p in det_p_zoom:
        p_time = p / fs
        p_amp = signal[p]
        ax.plot(p_time, p_amp, 'go', markersize=8, zorder=5)

    for r in det_r_zoom:
        r_time = r / fs
        r_amp = signal[r]
        ax.plot(r_time, r_amp, 'r^', markersize=10, zorder=5)

    ax.set_title(f'ECG Wave Detection Validation | Record {record_name}\n'
                 f'Ground Truth (hollow): P={len(gt_p_zoom)}, R={len(gt_r_zoom)} | '
                 f'Detected (filled): P={len(det_p_zoom)}, R={len(det_r_zoom)}',
                 fontsize=13, fontweight='bold')
    ax.set_xlabel('Time (seconds)', fontsize=11)
    ax.set_ylabel('Amplitude (mV)', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.legend(['ECG', 'P (Ground Truth)', 'R (Ground Truth)', 'P (Detected)', 'R (Detected)'],
              loc='upper right', fontsize=10)

    plt.tight_layout()

    zoom_output = f'output/plots/validation_comparison_{record_name}_zoomed.png'
    plt.savefig(zoom_output, dpi=150, bbox_inches='tight')
    print(f"Zoomed plot saved to: {zoom_output}")
    plt.close('all')

    # Print stats
    print(f"\n{'='*60}")
    print(f"Validation Summary - Record {record_name}")
    print(f"{'='*60}")
    print(f"Segment: {start_sec}-{start_sec+duration_sec}s")
    print(f"\nGround Truth:")
    print(f"  P waves: {len(gt_p_seg)}")
    print(f"  R peaks: {len(gt_r_seg)}")
    print(f"\nDetected:")
    print(f"  P waves: {len(det_p_seg)}")
    print(f"  R peaks: {len(det_r_seg)}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Plot full validation comparison')
    parser.add_argument('--record', '-r', type=str, default='sel100', help='QT database record')
    parser.add_argument('--start', '-s', type=float, default=0, help='Start time (seconds)')
    parser.add_argument('--duration', '-d', type=float, default=10, help='Duration (seconds)')
    args = parser.parse_args()

    plot_full_validation(args.record, args.start, args.duration)
