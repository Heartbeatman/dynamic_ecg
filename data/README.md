# ECG Data Formats

This directory contains ECG data organised by file format.

## Directory Structure

```
data/
├── csv/
│   ├── apple_watch/    # Apple Watch health export files
│   └── holter/         # Multi-channel Holter monitor exports
├── edf/                # European Data Format files
└── npz/                # Compressed numpy arrays
```

## File Formats

### CSV Files

#### Apple Watch Format
- **Location**: `csv/apple_watch/`
- **Format**: Single-lead ECG exported from Apple Health app
- **Structure**: Header rows followed by voltage samples
- **Sampling Rate**: Typically 512 Hz
- **Example**: `ecg_2021-12-17.csv`

#### Holter Monitor Format
- **Location**: `csv/holter/`
- **Format**: Multi-channel ECG data
- **Columns**: `time_seconds`, `channel_1`, `channel_2`, `channel_3`
- **Sampling Rate**: Variable (typically 180-360 Hz)
- **Example**: `full_ecg_data.csv`

### EDF Files
- **Location**: `edf/`
- **Format**: European Data Format (standard for physiological signals)
- **Channels**: Typically 3 leads
- **Metadata**: Sampling rate, units, patient info in header
- **Example**: `9ef19ac2-a4f6-4c95-9aaf-c709ed7cd958-edf-20240112041135.edf`

### NPZ Files
- **Location**: `npz/`
- **Format**: Compressed numpy arrays
- **Keys**: `ecg_1`, `ecg_2`, `ecg_3`, `fs` (sampling frequency)
- **Units**: Microvolts (μV)
- **Example**: `sample_ecg.npz`

## Loading Data

All formats can be loaded using the same interface:

```python
import data_utils as data

# Load any format
ecg = data.ecg_data('path/to/file.csv')  # or .edf, .npz
```

The loader automatically detects the format and creates `ecg_lead` objects for each channel.
