"""MIT-BIH Arrhythmia Database loader using wfdb library."""
import os
from typing import Optional, Tuple
import numpy as np
import wfdb

from ..core.ecg_lead import ECGLead


# Beat annotation symbols that represent actual heartbeats
BEAT_SYMBOLS = {
    'N', 'L', 'R', 'B', 'A', 'a', 'J', 'S', 'V', 'r', 'F', 'e', 'j', 'n', 'E', '/', 'f', 'Q', '?'
}


def load_mitbih_record(
    record_path: str,
    channel: int = 0
) -> Tuple[ECGLead, np.ndarray]:
    """
    Load a MIT-BIH record and its annotations.

    Args:
        record_path: Path to the record (without extension), e.g., 'data/mit-bih/100'
        channel: Channel index to load (0 or 1, default 0 for MLII lead)

    Returns:
        Tuple of (ECGLead object, ground_truth_peaks array)
        - ECGLead contains the signal data
        - ground_truth_peaks is array of sample indices for annotated beats
    """
    # Read the record
    record = wfdb.rdrecord(record_path)

    # Read annotations
    annotation = wfdb.rdann(record_path, 'atr')

    # Extract signal for the specified channel
    signal = record.p_signal[:, channel].astype(np.float64)
    fs = record.fs
    units = record.units[channel] if record.units else 'mV'

    # Filter annotations to only include beat symbols
    beat_mask = np.array([sym in BEAT_SYMBOLS for sym in annotation.symbol])
    ground_truth_peaks = annotation.sample[beat_mask]

    # Create ECGLead object
    lead = ECGLead(
        lead=channel,
        signal=signal,
        fs=fs,
        units=units
    )

    return lead, ground_truth_peaks


def load_mitbih_record_both_channels(
    record_path: str
) -> Tuple[ECGLead, ECGLead, np.ndarray]:
    """
    Load both channels of a MIT-BIH record.

    Args:
        record_path: Path to the record (without extension)

    Returns:
        Tuple of (lead_0, lead_1, ground_truth_peaks)
    """
    record = wfdb.rdrecord(record_path)
    annotation = wfdb.rdann(record_path, 'atr')

    fs = record.fs

    # Filter annotations to only include beat symbols
    beat_mask = np.array([sym in BEAT_SYMBOLS for sym in annotation.symbol])
    ground_truth_peaks = annotation.sample[beat_mask]

    lead_0 = ECGLead(
        lead=0,
        signal=record.p_signal[:, 0].astype(np.float64),
        fs=fs,
        units=record.units[0] if record.units else 'mV'
    )

    lead_1 = ECGLead(
        lead=1,
        signal=record.p_signal[:, 1].astype(np.float64),
        fs=fs,
        units=record.units[1] if record.units else 'mV'
    )

    return lead_0, lead_1, ground_truth_peaks


def list_mitbih_records(database_path: str) -> list:
    """
    List all available records in a MIT-BIH database directory.

    Args:
        database_path: Path to the database directory

    Returns:
        List of record names (without path or extension)
    """
    records = set()
    for filename in os.listdir(database_path):
        if filename.endswith('.dat'):
            record_name = filename[:-4]
            records.add(record_name)
    return sorted(list(records))


def get_record_info(record_path: str) -> dict:
    """
    Get metadata about a MIT-BIH record.

    Args:
        record_path: Path to the record (without extension)

    Returns:
        Dictionary with record metadata
    """
    record = wfdb.rdrecord(record_path)
    annotation = wfdb.rdann(record_path, 'atr')

    # Count beat types
    beat_mask = np.array([sym in BEAT_SYMBOLS for sym in annotation.symbol])
    beat_symbols = np.array(annotation.symbol)[beat_mask]

    beat_counts = {}
    for sym in beat_symbols:
        beat_counts[sym] = beat_counts.get(sym, 0) + 1

    return {
        'record_name': os.path.basename(record_path),
        'fs': record.fs,
        'n_sig': record.n_sig,
        'sig_len': record.sig_len,
        'duration_seconds': record.sig_len / record.fs,
        'duration_minutes': record.sig_len / record.fs / 60,
        'sig_name': record.sig_name,
        'units': record.units,
        'total_beats': len(beat_symbols),
        'beat_counts': beat_counts,
        'total_annotations': len(annotation.symbol)
    }
