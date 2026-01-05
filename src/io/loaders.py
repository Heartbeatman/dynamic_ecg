"""File loading functions for various ECG formats."""
import numpy as np
import pandas as pd
from pyedflib import highlevel
import concurrent.futures
from .apple_watch import csv_to_numpy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.ecg_data import ECGData


def _read_csv_metadata(file_path: str) -> dict:
    """Read metadata from CSV comment header lines."""
    meta = {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line.startswith('#'):
                break
            content = line[1:].strip()
            if ':' in content:
                key, value = content.split(':', 1)
                meta[key.strip()] = value.strip()
    return meta


def read_csv_data(ecg_data: 'ECGData') -> None:
    """
    Read ECG data from CSV file.
    Supports both Apple Watch single-lead and multi-channel Holter formats.
    Handles metadata comment lines starting with #.
    """
    from ..core.ecg_lead import ECGLead

    # Read metadata from comment header
    metadata = _read_csv_metadata(ecg_data.file_path)

    # Try to read as multi-channel CSV first
    try:
        # Skip comment lines when reading CSV
        df = pd.read_csv(ecg_data.file_path, comment='#')

        # Check if it's multi-channel format (has channel columns)
        if 'channel_1' in df.columns or 'channel_2' in df.columns or 'channel_3' in df.columns:
            # Multi-channel Holter CSV format
            # Use metadata sample_rate if available, else calculate from time column
            if 'sample_rate' in metadata:
                ecg_data.fs = int(metadata['sample_rate'])
            elif 'time_seconds' in df.columns and len(df) > 1:
                ecg_data.fs = int(round(1 / (df['time_seconds'][1] - df['time_seconds'][0])))
            else:
                ecg_data.fs = 200  # Default sampling rate

            # Use metadata units if available
            ecg_data.units = metadata.get('units', 'uV')

            if 'channel_1' in df.columns:
                ecg_data.lead_1 = ECGLead(
                    signal=df['channel_1'].values.astype(np.float64),
                    fs=ecg_data.fs,
                    units=ecg_data.units,
                    lead=0
                )
            if 'channel_2' in df.columns:
                ecg_data.lead_2 = ECGLead(
                    signal=df['channel_2'].values.astype(np.float64),
                    fs=ecg_data.fs,
                    units=ecg_data.units,
                    lead=1
                )
            if 'channel_3' in df.columns:
                ecg_data.lead_3 = ECGLead(
                    signal=df['channel_3'].values.astype(np.float64),
                    fs=ecg_data.fs,
                    units=ecg_data.units,
                    lead=2
                )
        else:
            # Apple Watch format
            data = csv_to_numpy(ecg_data.file_path)
            ecg_data.fs = data[1]
            ecg_data.units = 'uV'
            ecg_data.lead_1 = ECGLead(
                signal=data[0],
                fs=ecg_data.fs,
                units=ecg_data.units,
                lead=0
            )
    except:
        # Fall back to Apple Watch format
        data = csv_to_numpy(ecg_data.file_path)
        ecg_data.fs = data[1]
        ecg_data.units = 'uV'
        ecg_data.lead_1 = ECGLead(
            signal=data[0],
            fs=ecg_data.fs,
            units=ecg_data.units,
            lead=0
        )


def read_npz_data(ecg_data: 'ECGData') -> None:
    """Read ECG data from NPZ file."""
    from ..core.ecg_lead import ECGLead
    
    data = np.load(ecg_data.file_path)
    ecg_data.fs = int(data['fs'])
    ecg_data.units = 'uV'
    ecg_data.lead_1 = ECGLead(signal=data['ecg_1'], fs=ecg_data.fs, units=ecg_data.units, lead=0)
    ecg_data.lead_2 = ECGLead(signal=data['ecg_2'], fs=ecg_data.fs, units=ecg_data.units, lead=1)
    ecg_data.lead_3 = ECGLead(signal=data['ecg_3'], fs=ecg_data.fs, units=ecg_data.units, lead=2)


def read_edf_data(ecg_data: 'ECGData') -> None:
    """Read ECG data from EDF file."""
    from ..core.ecg_lead import ECGLead
    
    signals, signal_headers, header = highlevel.read_edf(ecg_data.file_path)
    # Check available keys
    print(f"Signal header keys: {signal_headers[0].keys()}")
    ecg_data.fs = signal_headers[0].get('sample_frequency', signal_headers[0].get('sample_rate'))
    ecg_data.units = signal_headers[0]['dimension']
    print(f'File: {ecg_data.file_path}')

    # Process the leads in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit tasks
        futures = [
            executor.submit(ECGLead, i, signals[i], ecg_data.fs, ecg_data.units)
            for i in range(3)
        ]

        # Wait for all futures to complete and collect results
        results = [future.result() for future in concurrent.futures.as_completed(futures)]

    # Assign the results using ECGLead.lead
    ecg_data.lead_1 = [result for result in results if result.lead == 0][0]
    ecg_data.lead_2 = [result for result in results if result.lead == 1][0]
    ecg_data.lead_3 = [result for result in results if result.lead == 2][0]