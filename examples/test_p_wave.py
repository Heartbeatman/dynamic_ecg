"""Test P-wave detection on MIT-BIH data."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt

from src.io.mitbih import load_mitbih_record
from src.processing import filters

# Path to MIT-BIH database
DATABASE_PATH = 'data/mit-bih-arrhythmia-database-1.0-2.0'


def test_p_wave_detection(record_name: str = '100', start_sec: float = 0, duration_sec: float = 10):
    """
    Test P-wave detection on a MIT-BIH record.

    Args:
        record_name: MIT-BIH record name
        start_sec: Start time in seconds
        duration_sec: Duration to analyse in seconds
    """
    record_path = os.path.join(DATABASE_PATH, record_name)

    # Load record
    lead, ground_truth_r = load_mitbih_record(record_path, channel=0)
    fs = lead.fs

    print(f"Record {record_name} loaded")
    print(f"Sample rate: {fs} Hz")
    print(f"Signal length: {len(lead.signal)} samples ({len(lead.signal)/fs:.1f} seconds)")

    # Extract segment
    start_sample = int(start_sec * fs)
    end_sample = int((start_sec + duration_sec) * fs)

    # Store raw signal for plotting
    raw_signal = lead.signal[start_sample:end_sample].copy()

    # Apply highpass filter
    lead.signal = filters.butter_highpass_filter(lead.signal, fs)

    # Detect R peaks first
    lead.r_wave_detector(adaptive=True)

    # Detect P waves
    lead.p_wave_detector()

    # Filter to segment
    r_in_segment = lead.r_peaks[(lead.r_peaks[:, 0] >= start_sample) & (lead.r_peaks[:, 0] < end_sample)]

    # P peaks is a 1D array after the refinement
    if lead.p_peaks is not None and len(lead.p_peaks) > 0:
        p_in_segment = lead.p_peaks[(lead.p_peaks >= start_sample) & (lead.p_peaks < end_sample)]
    else:
        p_in_segment = np.array([])

    print(f"\nIn segment {start_sec}-{start_sec + duration_sec}s:")
    print(f"  R peaks detected: {len(r_in_segment)}")
    print(f"  P peaks detected: {len(p_in_segment)}")

    # Create plot
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))

    time_axis = np.arange(start_sample, end_sample) / fs

    # Plot 1: Raw ECG with R peaks
    axes[0].plot(time_axis, raw_signal, 'b-', linewidth=0.8, label='ECG Signal')
    for r in r_in_segment:
        r_time = r[0] / fs
        if start_sample <= r[0] < end_sample:
            r_amp = raw_signal[int(r[0]) - start_sample]
            axes[0].plot(r_time, r_amp, 'r^', markersize=10)
            axes[0].axvline(x=r_time, color='red', alpha=0.3, linestyle='--')
    axes[0].set_title(f'Record {record_name} - R Peak Detection (N={len(r_in_segment)})', fontsize=12)
    axes[0].set_ylabel('Amplitude (mV)')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(['ECG', 'R peaks'], loc='upper right')

    # Plot 2: Raw ECG with P peaks
    axes[1].plot(time_axis, raw_signal, 'b-', linewidth=0.8, label='ECG Signal')
    for p in p_in_segment:
        p_time = p / fs
        if start_sample <= p < end_sample:
            p_amp = raw_signal[int(p) - start_sample]
            axes[1].plot(p_time, p_amp, 'g^', markersize=8)
            axes[1].axvline(x=p_time, color='green', alpha=0.3, linestyle='--')
    axes[1].set_title(f'P Wave Detection (N={len(p_in_segment)})', fontsize=12)
    axes[1].set_ylabel('Amplitude (mV)')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(['ECG', 'P peaks'], loc='upper right')

    # Plot 3: Phasor transform
    phasor_segment = lead.phasor[start_sample:end_sample]
    axes[2].plot(time_axis, phasor_segment, 'purple', linewidth=0.8)
    axes[2].axhline(y=lead.threshold, color='orange', linestyle='--', label=f'Threshold={lead.threshold:.4f}')
    axes[2].set_title('Phasor Transform', fontsize=12)
    axes[2].set_xlabel('Time (seconds)')
    axes[2].set_ylabel('Phase (radians)')
    axes[2].grid(True, alpha=0.3)
    axes[2].legend(loc='upper right')

    plt.tight_layout()

    # Save figure
    output_path = f'p_wave_test_{record_name}_{start_sec}-{start_sec+duration_sec}s.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to: {output_path}")
    plt.close()

    return lead


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test P-wave detection')
    parser.add_argument('--record', '-r', type=str, default='100', help='MIT-BIH record name')
    parser.add_argument('--start', '-s', type=float, default=0, help='Start time in seconds')
    parser.add_argument('--duration', '-d', type=float, default=10, help='Duration in seconds')
    args = parser.parse_args()

    test_p_wave_detection(args.record, args.start, args.duration)
