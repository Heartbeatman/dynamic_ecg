"""Plot P-wave detection validation against QT Database ground truth."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt
import wfdb

from src.processing import filters, transforms

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


def plot_p_wave_validation(record_name='sel100', start_sec=0, duration_sec=10):
    """Plot P-wave detection vs ground truth."""
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

    # Detect P waves
    detected_p = detect_p_waves_windowed(filtered_signal, r_peak_gt, fs, rv=0.001)

    # Extract segment
    start_sample = int(start_sec * fs)
    end_sample = int((start_sec + duration_sec) * fs)
    segment = signal[start_sample:end_sample]
    time_axis = np.arange(len(segment)) / fs + start_sec

    # Filter to segment
    gt_p_in_seg = p_wave_gt[(p_wave_gt >= start_sample) & (p_wave_gt < end_sample)]
    det_p_in_seg = detected_p[(detected_p >= start_sample) & (detected_p < end_sample)]
    r_in_seg = r_peak_gt[(r_peak_gt >= start_sample) & (r_peak_gt < end_sample)]

    # Match detections to ground truth
    tolerance_samples = int(75 * fs / 1000)  # 75ms
    matched_gt = set()
    matched_det = set()

    for i, gt in enumerate(gt_p_in_seg):
        if len(det_p_in_seg) == 0:
            continue
        distances = np.abs(det_p_in_seg - gt)
        min_idx = np.argmin(distances)
        if distances[min_idx] <= tolerance_samples and min_idx not in matched_det:
            matched_gt.add(i)
            matched_det.add(min_idx)

    # Create plot
    fig, axes = plt.subplots(2, 1, figsize=(16, 8))

    # Plot 1: Ground truth P waves
    axes[0].plot(time_axis, segment, 'b-', linewidth=0.8)
    for i, p in enumerate(gt_p_in_seg):
        p_time = p / fs
        p_amp = signal[p]
        color = 'green' if i in matched_gt else 'red'
        marker = 'o' if i in matched_gt else 'x'
        axes[0].plot(p_time, p_amp, marker, color=color, markersize=8)
        axes[0].axvline(x=p_time, color=color, alpha=0.2, linestyle='--')

    for r in r_in_seg:
        r_time = r / fs
        r_amp = signal[r]
        axes[0].plot(r_time, r_amp, 'r^', markersize=8)

    axes[0].set_title(f'Ground Truth P Waves (green=matched, red=missed) | Record {record_name}', fontsize=12)
    axes[0].set_ylabel('Amplitude (mV)')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(['ECG', 'P (matched)', 'P (missed)', 'R peak'], loc='upper right')

    # Plot 2: Detected P waves
    axes[1].plot(time_axis, segment, 'b-', linewidth=0.8)
    for i, p in enumerate(det_p_in_seg):
        p_time = p / fs
        p_amp = signal[p]
        color = 'green' if i in matched_det else 'orange'
        marker = 'o' if i in matched_det else 's'
        axes[1].plot(p_time, p_amp, marker, color=color, markersize=8)
        axes[1].axvline(x=p_time, color=color, alpha=0.2, linestyle='--')

    for r in r_in_seg:
        r_time = r / fs
        r_amp = signal[r]
        axes[1].plot(r_time, r_amp, 'r^', markersize=8)

    axes[1].set_title(f'Detected P Waves (green=TP, orange=FP) | GT: {len(gt_p_in_seg)}, Det: {len(det_p_in_seg)}', fontsize=12)
    axes[1].set_xlabel('Time (seconds)')
    axes[1].set_ylabel('Amplitude (mV)')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(['ECG', 'P (TP)', 'P (FP)', 'R peak'], loc='upper right')

    plt.tight_layout()

    output_path = f'p_wave_validation_{record_name}_{start_sec}-{start_sec+duration_sec}s.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")
    plt.close()

    # Print segment stats
    tp = len(matched_gt)
    fp = len(det_p_in_seg) - len(matched_det)
    fn = len(gt_p_in_seg) - len(matched_gt)
    print(f"Segment {start_sec}-{start_sec+duration_sec}s: TP={tp}, FP={fp}, FN={fn}")


if __name__ == '__main__':
    plot_p_wave_validation('sel100', start_sec=0, duration_sec=10)
    plot_p_wave_validation('sel100', start_sec=60, duration_sec=10)  # Another segment
