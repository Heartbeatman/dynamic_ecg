"""Test P-wave detection using windowed search before R peaks."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt

from src.io.mitbih import load_mitbih_record
from src.processing import filters, transforms

# Path to MIT-BIH database
DATABASE_PATH = 'data/mit-bih-arrhythmia-database-1.0-2.0'


def detect_p_waves_windowed(
    signal: np.ndarray,
    r_peaks: np.ndarray,
    fs: int,
    rv: float = 0.001,
    window_start_ms: float = 250,
    window_end_ms: float = 50
) -> np.ndarray:
    """
    Detect P waves by searching in a window before each R peak.

    Args:
        signal: Filtered ECG signal
        r_peaks: Array of R peak locations (sample indices)
        fs: Sampling frequency
        rv: Reference value for phasor transform
        window_start_ms: Start of search window before R peak (ms)
        window_end_ms: End of search window before R peak (ms)

    Returns:
        Array of P wave locations (sample indices)
    """
    # Convert window to samples
    window_start_samples = int(window_start_ms * fs / 1000)
    window_end_samples = int(window_end_ms * fs / 1000)

    # Compute phasor transform on full signal
    phasor = transforms.phasor_transform(signal, rv=rv)

    p_waves = []

    for r_idx in r_peaks:
        r_sample = int(r_idx)

        # Define search window (before R peak)
        search_start = max(0, r_sample - window_start_samples)
        search_end = max(0, r_sample - window_end_samples)

        if search_end <= search_start:
            continue

        # Extract window from phasor transform
        window = phasor[search_start:search_end]

        if len(window) == 0:
            continue

        # Find the maximum in the window (P wave peak)
        max_idx = np.argmax(window)
        p_sample = search_start + max_idx

        p_waves.append(p_sample)

    return np.array(p_waves)


def test_windowed_detection(record_name: str = '100', start_sec: float = 0, duration_sec: float = 10):
    """Test windowed P-wave detection."""
    record_path = os.path.join(DATABASE_PATH, record_name)

    # Load record
    lead, _ = load_mitbih_record(record_path, channel=0)
    fs = lead.fs

    # Apply highpass filter
    lead.signal = filters.butter_highpass_filter(lead.signal, fs)

    # Detect R peaks first
    lead.r_wave_detector(adaptive=True)

    # Extract segment bounds
    start_sample = int(start_sec * fs)
    end_sample = int((start_sec + duration_sec) * fs)

    # Get R peaks in segment
    r_in_segment = lead.r_peaks[(lead.r_peaks[:, 0] >= start_sample) & (lead.r_peaks[:, 0] < end_sample)]
    r_indices = r_in_segment[:, 0]

    # Detect P waves using windowed approach
    p_waves = detect_p_waves_windowed(lead.signal, r_indices, fs, rv=0.001)

    print(f"Record {record_name}, segment {start_sec}-{start_sec+duration_sec}s")
    print(f"R peaks detected: {len(r_in_segment)}")
    print(f"P waves detected: {len(p_waves)}")

    # Compute phasor for plotting
    phasor = transforms.phasor_transform(lead.signal, rv=0.001)

    # Create plot
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))

    # Extract segment for plotting
    segment = lead.signal[start_sample:end_sample]
    phasor_segment = phasor[start_sample:end_sample]
    time_axis = np.arange(len(segment)) / fs + start_sec

    # Plot 1: ECG with R peaks and P waves
    axes[0].plot(time_axis, segment, 'b-', linewidth=0.8, label='ECG')

    # Plot R peaks
    for r in r_indices:
        if start_sample <= r < end_sample:
            r_time = r / fs
            r_amp = lead.signal[int(r)]
            axes[0].plot(r_time, r_amp, 'r^', markersize=10)
            axes[0].axvline(x=r_time, color='red', alpha=0.2, linestyle='-')

    # Plot P waves
    for p in p_waves:
        if start_sample <= p < end_sample:
            p_time = p / fs
            p_amp = lead.signal[int(p)]
            axes[0].plot(p_time, p_amp, 'go', markersize=8)
            axes[0].axvline(x=p_time, color='green', alpha=0.2, linestyle='--')

    axes[0].set_title(f'Record {record_name} - R peaks (red) and P waves (green)', fontsize=12)
    axes[0].set_ylabel('Amplitude (mV)')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(['ECG', 'R peak', 'P wave'], loc='upper right')

    # Plot 2: Phasor transform with search windows
    axes[1].plot(time_axis, phasor_segment, 'purple', linewidth=0.8)

    # Show search windows
    window_start_ms = 250
    window_end_ms = 50
    for r in r_indices:
        if start_sample <= r < end_sample:
            r_time = r / fs
            win_start_time = (r - int(window_start_ms * fs / 1000)) / fs
            win_end_time = (r - int(window_end_ms * fs / 1000)) / fs
            axes[1].axvspan(win_start_time, win_end_time, alpha=0.2, color='yellow')

    # Mark P waves on phasor
    for p in p_waves:
        if start_sample <= p < end_sample:
            p_time = p / fs
            p_phasor = phasor[int(p)]
            axes[1].plot(p_time, p_phasor, 'go', markersize=8)

    axes[1].set_title(f'Phasor Transform (rv=0.001) with PR search windows (yellow)', fontsize=12)
    axes[1].set_ylabel('Phase (radians)')
    axes[1].grid(True, alpha=0.3)

    # Plot 3: Zoomed view of a few beats
    zoom_start = start_sec
    zoom_end = start_sec + 3  # First 3 seconds
    zoom_mask = (time_axis >= zoom_start) & (time_axis < zoom_end)
    zoom_time = time_axis[zoom_mask]
    zoom_signal = segment[zoom_mask]

    axes[2].plot(zoom_time, zoom_signal, 'b-', linewidth=1.0)

    # Plot R and P peaks in zoom
    for r in r_indices:
        r_time = r / fs
        if zoom_start <= r_time < zoom_end:
            r_amp = lead.signal[int(r)]
            axes[2].plot(r_time, r_amp, 'r^', markersize=12, label='R peak')
            axes[2].annotate('R', (r_time, r_amp + 0.05), ha='center', fontsize=10, color='red')

    for p in p_waves:
        p_time = p / fs
        if zoom_start <= p_time < zoom_end:
            p_amp = lead.signal[int(p)]
            axes[2].plot(p_time, p_amp, 'go', markersize=10, label='P wave')
            axes[2].annotate('P', (p_time, p_amp + 0.05), ha='center', fontsize=10, color='green')

    axes[2].set_title(f'Zoomed View ({zoom_start}-{zoom_end}s) - P wave precedes R peak', fontsize=12)
    axes[2].set_xlabel('Time (seconds)')
    axes[2].set_ylabel('Amplitude (mV)')
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()

    output_path = f'p_wave_windowed_{record_name}_{start_sec}-{start_sec+duration_sec}s.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to: {output_path}")
    plt.close()

    # Print PR intervals
    print(f"\nPR Intervals:")
    for i, (p, r) in enumerate(zip(p_waves, r_indices)):
        pr_ms = (r - p) / fs * 1000
        print(f"  Beat {i+1}: P at {p/fs:.3f}s, R at {r/fs:.3f}s, PR interval = {pr_ms:.1f}ms")


if __name__ == '__main__':
    test_windowed_detection('100', start_sec=0, duration_sec=10)
