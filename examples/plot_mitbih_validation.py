"""Plot R-peak and P-wave detection validation against MIT-BIH ground truth."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt

from src.io.mitbih import load_mitbih_record
from src.processing import filters, transforms

MITBIH_PATH = 'data/mit-bih-arrhythmia-database-1.0-2.0'


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


def plot_mitbih_validation(record_name='100', start_sec=0, duration_sec=10):
    """
    Create validation plot showing Ground Truth vs Detected R peaks for MIT-BIH.
    """
    record_path = os.path.join(MITBIH_PATH, record_name)

    # Load record and ground truth
    lead, ground_truth_r = load_mitbih_record(record_path, channel=0)
    signal = lead.signal.copy()
    fs = lead.fs

    # Apply highpass filter
    lead.signal = filters.butter_highpass_filter(lead.signal, fs)

    # Detect R peaks
    lead.r_wave_detector(adaptive=True)
    detected_r = lead.r_peaks[:, 0].astype(int)

    # Extract segment
    start_sample = int(start_sec * fs)
    end_sample = int((start_sec + duration_sec) * fs)
    segment = signal[start_sample:end_sample]
    time_axis = np.arange(len(segment)) / fs + start_sec

    # Filter to segment
    gt_r_seg = ground_truth_r[(ground_truth_r >= start_sample) & (ground_truth_r < end_sample)]
    det_r_seg = detected_r[(detected_r >= start_sample) & (detected_r < end_sample)]

    # Match detections to ground truth
    tolerance_samples = int(150 * fs / 1000)  # 150ms
    matched_gt = set()
    matched_det = set()

    for i, gt in enumerate(gt_r_seg):
        if len(det_r_seg) == 0:
            continue
        distances = np.abs(det_r_seg - gt)
        min_idx = np.argmin(distances)
        if distances[min_idx] <= tolerance_samples and min_idx not in matched_det:
            matched_gt.add(i)
            matched_det.add(min_idx)

    tp = len(matched_gt)
    fp = len(det_r_seg) - len(matched_det)
    fn = len(gt_r_seg) - len(matched_gt)

    # Create figure
    fig, axes = plt.subplots(3, 1, figsize=(16, 12))

    # ===== Plot 1: Ground Truth =====
    ax1 = axes[0]
    ax1.plot(time_axis, segment, 'b-', linewidth=0.8)

    for r in gt_r_seg:
        r_time = r / fs
        r_amp = signal[r]
        ax1.plot(r_time, r_amp, 'r^', markersize=12, zorder=5)
        ax1.axvline(x=r_time, color='red', alpha=0.2, linestyle='-')

    ax1.set_title(f'Ground Truth R Peaks | MIT-BIH Record {record_name} | Count: {len(gt_r_seg)}',
                  fontsize=14, fontweight='bold')
    ax1.set_ylabel('Amplitude (mV)', fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.legend(['ECG', 'R peak (Ground Truth)'], loc='upper right', fontsize=10)

    # ===== Plot 2: Our Detection =====
    ax2 = axes[1]
    ax2.plot(time_axis, segment, 'b-', linewidth=0.8)

    for i, r in enumerate(det_r_seg):
        r_time = r / fs
        r_amp = signal[r]
        color = 'green' if i in matched_det else 'orange'
        ax2.plot(r_time, r_amp, '^', color=color, markersize=12, zorder=5)
        ax2.axvline(x=r_time, color=color, alpha=0.2, linestyle='-')

    ax2.set_title(f'Detected R Peaks | Count: {len(det_r_seg)} (TP: {tp}, FP: {fp})',
                  fontsize=14, fontweight='bold')
    ax2.set_ylabel('Amplitude (mV)', fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.legend(['ECG', 'R peak (TP)', 'R peak (FP)'], loc='upper right', fontsize=10)

    # ===== Plot 3: Overlay Comparison =====
    ax3 = axes[2]
    ax3.plot(time_axis, segment, 'b-', linewidth=0.8)

    # Ground truth - hollow red markers
    for i, r in enumerate(gt_r_seg):
        r_time = r / fs
        r_amp = signal[r]
        color = 'green' if i in matched_gt else 'red'
        ax3.plot(r_time, r_amp, '^', markersize=16, markerfacecolor='none',
                 markeredgecolor=color, markeredgewidth=2.5, zorder=4)

    # Detected - filled markers
    for i, r in enumerate(det_r_seg):
        r_time = r / fs
        r_amp = signal[r]
        color = 'green' if i in matched_det else 'orange'
        ax3.plot(r_time, r_amp, '^', color=color, markersize=8, zorder=5)

    ax3.set_title(f'Overlay: Ground Truth (hollow) vs Detected (filled) | TP: {tp}, FP: {fp}, FN: {fn}',
                  fontsize=14, fontweight='bold')
    ax3.set_xlabel('Time (seconds)', fontsize=11)
    ax3.set_ylabel('Amplitude (mV)', fontsize=11)
    ax3.grid(True, alpha=0.3)
    ax3.legend(['ECG', 'Matched (GT)', 'Missed (FN)', 'TP (Det)', 'FP (Det)'],
               loc='upper right', fontsize=10)

    plt.tight_layout()

    # Save figure
    os.makedirs('output/plots', exist_ok=True)
    output_path = f'output/plots/mitbih_validation_{record_name}_{start_sec}-{start_sec+duration_sec}s.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")

    # Detect P waves using detected R peaks
    detected_p = detect_p_waves_windowed(lead.signal, detected_r, fs, rv=0.001)
    det_p_seg = detected_p[(detected_p >= start_sample) & (detected_p < end_sample)]

    # Zoomed version - clean comparison with P waves
    fig2, ax = plt.subplots(figsize=(16, 6))

    zoom_duration = min(5, duration_sec)
    zoom_end_sample = int((start_sec + zoom_duration) * fs)
    zoom_segment = signal[start_sample:zoom_end_sample]
    zoom_time = np.arange(len(zoom_segment)) / fs + start_sec

    ax.plot(zoom_time, zoom_segment, 'b-', linewidth=1.0, label='ECG Signal')

    gt_r_zoom = gt_r_seg[gt_r_seg < zoom_end_sample]
    det_r_zoom = det_r_seg[det_r_seg < zoom_end_sample]
    det_p_zoom = det_p_seg[det_p_seg < zoom_end_sample]

    # Ground truth R peaks - purple with dotted vertical lines
    for i, r in enumerate(gt_r_zoom):
        r_time = r / fs
        r_amp = signal[r]
        ax.axvline(x=r_time, color='purple', alpha=0.4, linestyle=':', linewidth=2)
        ax.plot(r_time, r_amp, 'v', markersize=14, markerfacecolor='none',
                markeredgecolor='purple', markeredgewidth=2.5, zorder=4)

    # Detected R peaks - green filled triangles
    for i, r in enumerate(det_r_zoom):
        r_time = r / fs
        r_amp = signal[r]
        ax.plot(r_time, r_amp, 'g^', markersize=10, zorder=5)

    # Detected P waves - orange circles
    for i, p in enumerate(det_p_zoom):
        p_time = p / fs
        p_amp = signal[p]
        ax.plot(p_time, p_amp, 'o', color='orange', markersize=10, zorder=5)

    se = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0
    ppv = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0

    ax.set_title(f'MIT-BIH Record {record_name} | R Peak and P Wave Detection\n'
                 f'R peaks - GT: {len(gt_r_zoom)}, Det: {len(det_r_zoom)} | '
                 f'P waves Det: {len(det_p_zoom)} | Se: {se:.1f}%, PPV: {ppv:.1f}%',
                 fontsize=13, fontweight='bold')
    ax.set_xlabel('Time (seconds)', fontsize=11)
    ax.set_ylabel('Amplitude (mV)', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.legend(['ECG', 'R Ground Truth', 'R Detected', 'P Detected'], loc='upper right', fontsize=10)

    plt.tight_layout()

    zoom_output = f'output/plots/mitbih_validation_{record_name}_zoomed.png'
    plt.savefig(zoom_output, dpi=150, bbox_inches='tight')
    print(f"Zoomed plot saved to: {zoom_output}")
    plt.close('all')

    # Print stats
    print(f"\n{'='*60}")
    print(f"MIT-BIH Record {record_name} Validation")
    print(f"{'='*60}")
    print(f"Segment: {start_sec}-{start_sec+duration_sec}s")
    print(f"Ground Truth R peaks: {len(gt_r_seg)}")
    print(f"Detected R peaks: {len(det_r_seg)}")
    print(f"TP: {tp}, FP: {fp}, FN: {fn}")
    print(f"Sensitivity: {se:.2f}%")
    print(f"PPV: {ppv:.2f}%")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Plot MIT-BIH R peak validation')
    parser.add_argument('--record', '-r', type=str, default='100', help='MIT-BIH record')
    parser.add_argument('--start', '-s', type=float, default=0, help='Start time (seconds)')
    parser.add_argument('--duration', '-d', type=float, default=10, help='Duration (seconds)')
    args = parser.parse_args()

    plot_mitbih_validation(args.record, args.start, args.duration)
