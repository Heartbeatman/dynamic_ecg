"""Test P-wave detection with different rv values."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt

from src.io.mitbih import load_mitbih_record
from src.processing import filters, transforms, detectors

# Path to MIT-BIH database
DATABASE_PATH = 'data/mit-bih-arrhythmia-database-1.0-2.0'


def test_rv_values(record_name: str = '100', start_sec: float = 0, duration_sec: float = 10):
    """Test different rv values for phasor transform."""
    record_path = os.path.join(DATABASE_PATH, record_name)

    # Load record
    lead, _ = load_mitbih_record(record_path, channel=0)
    fs = lead.fs

    # Extract segment
    start_sample = int(start_sec * fs)
    end_sample = int((start_sec + duration_sec) * fs)

    # Apply highpass filter
    filtered_signal = filters.butter_highpass_filter(lead.signal, fs)
    segment = filtered_signal[start_sample:end_sample]
    raw_segment = lead.signal[start_sample:end_sample]

    # Test different rv values
    rv_values = [0.001, 0.01, 0.1, 0.5, 1.0]

    fig, axes = plt.subplots(len(rv_values) + 1, 1, figsize=(14, 3 * (len(rv_values) + 1)))

    time_axis = np.arange(len(segment)) / fs + start_sec

    # Plot raw ECG
    axes[0].plot(time_axis, raw_segment, 'b-', linewidth=0.8)
    axes[0].set_title(f'Record {record_name} - Raw ECG Signal', fontsize=12)
    axes[0].set_ylabel('Amplitude (mV)')
    axes[0].grid(True, alpha=0.3)

    print(f"Signal stats: min={segment.min():.4f}, max={segment.max():.4f}, std={segment.std():.4f}")
    print(f"\nTesting rv values:")
    print("-" * 60)

    for i, rv in enumerate(rv_values):
        # Compute phasor transform
        phasor = transforms.phasor_transform(segment, rv=rv)

        # Calculate threshold
        threshold = phasor.max() / 4

        # Detect peaks
        peaks = detectors.peak_core(phasor, threshold)

        print(f"rv={rv:6.3f} | Phasor range: [{phasor.min():.3f}, {phasor.max():.3f}] | "
              f"Threshold: {threshold:.3f} | Peaks detected: {len(peaks)}")

        # Plot
        ax = axes[i + 1]
        ax.plot(time_axis, phasor, 'purple', linewidth=0.8)
        ax.axhline(y=threshold, color='orange', linestyle='--', label=f'Threshold={threshold:.3f}')

        # Mark detected peaks
        if len(peaks) > 0:
            peak_times = peaks[:, 0] / fs + start_sec
            peak_amps = phasor[peaks[:, 0].astype(int)]
            ax.plot(peak_times, peak_amps, 'g^', markersize=6)

        ax.set_title(f'rv = {rv} | Peaks detected: {len(peaks)}', fontsize=11)
        ax.set_ylabel('Phase (rad)')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right')

    axes[-1].set_xlabel('Time (seconds)')

    plt.tight_layout()

    output_path = f'p_wave_rv_comparison_{record_name}.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to: {output_path}")
    plt.close()


if __name__ == '__main__':
    test_rv_values('100', start_sec=0, duration_sec=10)
