"""ECG lead dataclass and processing."""
from dataclasses import dataclass
from typing import Optional
import numpy as np
from ..processing import detectors, transforms
from ..processing.transforms import timer_decorator
from ..analysis import metrics
from ..visualisation import plots


@dataclass
class ECGLead:
    """Represents a single ECG lead/channel with automatic processing."""
    lead: int
    signal: np.ndarray
    fs: int
    units: str
    r_peaks: Optional[np.ndarray] = None
    p_peaks: Optional[np.ndarray] = None
    refined_p: Optional[np.ndarray] = None
    t_peaks: Optional[np.ndarray] = None
    window: Optional[np.ndarray] = None
    phasor: Optional[np.ndarray] = None
    threshold: Optional[float] = None
    rr_int: Optional[np.ndarray] = None
    frequency_bins: Optional[np.ndarray] = None
    time_bins: Optional[np.ndarray] = None

    # Stats
    bpm: Optional[float] = None
    correlation_coefficient: Optional[float] = None

    def __post_init__(self):
        """Performs signal preprocessing and R wave detection on the ECG signal."""
        self._signal_preprocessing()
        self.r_wave_detector()
        self.p_wave_detector()
        self.calculate_rr_int()
        self.r_stats()

    def _signal_preprocessing(self):
        """Performs signal preprocessing on the ECG signal."""
        if self.signal.shape[0] > 1e6:
            print('Signal too long, slicing to 5 minutes')
            window_slice = int(60 * self.fs * 5)
            self.signal = self.signal[window_slice:-window_slice] / 1000
        else:
            print('Signal not too long, not slicing')
            self.signal = self.signal / 1000
        
        if self.units == 'uV':
            self.signal = self.signal

    @timer_decorator
    def threshold_calc(self, transformed_signal):
        """Calculate the threshold for the R peak detector."""
        # Calculate the mean of the transformed signal
        transformed_signal = transformed_signal[(transformed_signal > 0.01) & (transformed_signal < 2)]
        return transformed_signal.mean() / 4

    @timer_decorator
    def r_wave_detector(self):
        """Detect the R peaks of the signal."""
        # Window is the transformed signal
        self.window = transforms.grad_square_conv(self.signal, self.fs, sin_wave=False)
        # Calculate the threshold
        self.threshold = self.threshold_calc(self.window)
        # Perform the peak detection on this transformed signal
        self.r_peaks = detectors.peak(signal=self.window, threshold=self.threshold)

    @timer_decorator
    def calculate_rr_int(self):
        """Calculate the RR intervals from the R peak positions."""
        self.rr_int = np.diff(self.r_peaks[:, 0], prepend=0)

    @timer_decorator
    def p_wave_detector(self):
        """Detect the P peaks of the signal."""
        # Phasor transform
        self.phasor = transforms.phasor_transform(self.signal, rv=0.001)
        # Calculate the threshold
        self.threshold = self.threshold_calc(self.phasor)
        # Perform the peak detection on this transformed signal
        self.p_peaks = detectors.peak(signal=self.phasor, threshold=self.threshold)
        
        # Combine and sort R peaks and P peaks
        combined_peaks = np.sort(np.concatenate((self.r_peaks[:, 0], self.p_peaks[:, 0])))

        # Identify unique peaks that are close to each other
        close_peaks_indices = np.where(np.diff(combined_peaks) < 10)[0]

        # Create an array of indices to add to the close peaks
        additional_indices = close_peaks_indices + 1

        # Combine and sort the unique and additional indices
        refined_peaks_indices = np.sort(np.concatenate((close_peaks_indices, additional_indices)))

        self.p_peaks = np.delete(combined_peaks, refined_peaks_indices)

    def r_plot(self):
        """Plot the ECG signal and the R peaks."""
        plots.r_plotting(self)
        plots.lorenz_plot(self)

    def r_stats(self):
        """Calculate R wave statistics."""
        # Calculate Pearson's correlation coefficient
        self.correlation_coefficient = np.corrcoef(self.rr_int[:-1], self.rr_int[1:])[0, 1]
        # BPM calculation
        self.bpm = 2 * self.r_peaks[:, 0].shape[0]

    def p_plot(self):
        """Plot the ECG signal and the P peaks."""
        plots.p_plotting(self)