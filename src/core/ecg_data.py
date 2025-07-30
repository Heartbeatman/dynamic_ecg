"""ECG data container for multi-lead recordings."""
from dataclasses import dataclass
from typing import Optional
import numpy as np
import concurrent.futures
from .ecg_lead import ECGLead
from ..io import loaders


@dataclass
class ECGData:
    """ECG data class to read ECG data from various file formats."""
    file_path: str
    fs: Optional[int] = None
    units: Optional[str] = None
    lead_1: Optional[ECGLead] = None
    lead_2: Optional[ECGLead] = None
    lead_3: Optional[ECGLead] = None
    common_beats: Optional[np.ndarray] = None

    def __post_init__(self):
        """Reads the ECG data from the file."""
        self._read_data()

    def _read_data(self):
        """Reads the ECG data from the file based on extension."""
        if self.file_path.endswith('.npz'):
            self._read_npz_data()
        elif self.file_path.endswith('.edf'):
            self._read_edf_data()
        elif self.file_path.endswith('.csv'):
            self._read_csv_data()

    def _read_csv_data(self):
        """Reads ECG data from CSV file."""
        loaders.read_csv_data(self)

    def _read_npz_data(self):
        """Reads ECG data from NPZ file."""
        loaders.read_npz_data(self)

    def _read_edf_data(self):
        """Reads ECG data from EDF file."""
        loaders.read_edf_data(self)