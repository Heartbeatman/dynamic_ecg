"""Compare legacy vs Pan-Tompkins adaptive R peak detection."""

import sys

sys.path.insert(0, "..")

import os

import matplotlib.pyplot as plt
import numpy as np

from src.core import ECGData

# Files to process
FILES = [
    "data/examples/holter_sample.csv",
    "data/csv/holter/Second_Good_dry.csv",
    "data/csv/holter/good_Dry_data.csv",
    "data/csv/holter/ecg_20251210_100521dr80v2.csv",
    "data/edf/9ef19ac2-a4f6-4c95-9aaf-c709ed7cd958-edf-20240112041135.edf",
]


def compare_detectors(filepath: str) -> None:
    """Generate comparison plot for a single file."""
    filename = os.path.basename(filepath).replace(".csv", "")
    print(f"\nProcessing: {filename}")

    # Load data twice for comparison
    ecg_legacy = ECGData(file_path=filepath)
    ecg_adaptive = ECGData(file_path=filepath)

    print(f"  fs={ecg_adaptive.lead_2.fs}Hz, samples={len(ecg_adaptive.lead_2.signal)}")

    # Run detectors
    ecg_legacy.lead_2.r_wave_detector(adaptive=False)
    ecg_adaptive.lead_2.r_wave_detector(adaptive=True)

    # Get data
    signal = ecg_adaptive.lead_2.signal
    fs = ecg_adaptive.lead_2.fs
    time = np.arange(len(signal)) / fs

    legacy_peaks = ecg_legacy.lead_2.r_peaks[:, 0].astype(int)
    adaptive_peaks = ecg_adaptive.lead_2.r_peaks[:, 0].astype(int)

    print(f"  Legacy: {len(legacy_peaks)} peaks, Adaptive: {len(adaptive_peaks)} peaks")

    # Create comparison plot
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    axes[0].plot(time, signal, "k-", linewidth=0.5)
    axes[0].scatter(
        time[legacy_peaks],
        signal[legacy_peaks],
        c="red",
        s=60,
        marker="x",
        linewidths=2,
        label=f"R Peaks (n={len(legacy_peaks)})",
    )
    axes[0].set_ylabel("Amplitude")
    axes[0].set_title(f"{filename} - Legacy Fixed Threshold")
    axes[0].legend(loc="upper right")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(time, signal, "k-", linewidth=0.5)
    axes[1].scatter(
        time[adaptive_peaks],
        signal[adaptive_peaks],
        c="blue",
        s=60,
        marker="x",
        linewidths=2,
        label=f"R Peaks (n={len(adaptive_peaks)})",
    )
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("Amplitude")
    axes[1].set_title(f"{filename} - Pan-Tompkins Adaptive")
    axes[1].legend(loc="upper right")
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    outpath = f"output/{filename}_comparison.png"
    plt.savefig(outpath, dpi=150)
    plt.close()
    print(f"  Saved: {outpath}")


if __name__ == "__main__":
    os.chdir("/Users/kevindejbod/dynamic_ecg")

    for filepath in FILES:
        try:
            compare_detectors(filepath)
        except Exception as e:
            print(f"  Error: {e}")

    print("\nDone!")
