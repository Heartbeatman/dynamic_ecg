"""ECG lead dataclass and processing."""
from dataclasses import dataclass
from typing import Optional
import numpy as np
from ..processing import detectors, transforms, filters
from ..processing.transforms import timer_decorator
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

    def __post_init__(self) -> None:
        """Performs signal preprocessing and R wave detection on the ECG signal."""
        #self._signal_preprocessing()
        #self.r_wave_detector()
        #self.p_wave_detector()
        #self.calculate_rr_int()
        #self.r_stats()

    def _signal_preprocessing(self) -> None:
        """Performs signal preprocessing on the ECG signal."""
        # Slice if signal is too long
        if self.signal.shape[0] > 1e6:
            print('Signal too long, slicing to 5 minutes')
            window_slice = int(60 * self.fs * 5)
            self.signal = self.signal[window_slice:-window_slice]

        # Scale signal
        self.signal = self.signal / 1000

        # Apply highpass filter to remove baseline wander
        self.signal = filters.butter_highpass_filter(self.signal, self.fs)

    @timer_decorator
    def threshold_calc(self, transformed_signal: np.ndarray) -> float:
        """Calculate the threshold for the R peak detector."""
        # Use max-based threshold - more robust for varying signal magnitudes
        # R-peaks typically have the highest gradient, so max/4 catches them
        # while ignoring smaller P and T waves
        return transformed_signal.max() / 4

    @timer_decorator
    def r_wave_detector(self, adaptive: bool = True) -> None:
        """
        Detect the R peaks of the signal.

        Args:
            adaptive: Use Pan-Tompkins adaptive thresholding (default True)
        """
        # Apply bandpass filter if using adaptive detection
        if adaptive:
            filtered_signal = filters.butter_bandpass_filter(self.signal, self.fs)
        else:
            filtered_signal = self.signal

        # Transform: derivative, squaring, moving window integration
        self.window = transforms.grad_square_conv(filtered_signal, self.fs, sin_wave=False)

        if adaptive:
            # Pan-Tompkins adaptive threshold detection
            self.r_peaks = detectors.adaptive_peak_detect(self.window, self.fs)
        else:
            # Legacy fixed threshold detection
            self.threshold = self.threshold_calc(self.window)
            self.r_peaks = detectors.peak(signal=self.window, threshold=self.threshold)

    @timer_decorator
    def calculate_rr_int(self) -> None:
        """Calculate the RR intervals from the R peak positions."""
        self.rr_int = np.diff(self.r_peaks[:, 0], prepend=0)

    @timer_decorator
    def p_wave_detector(self) -> None:
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

    def r_plot(self) -> None:
        """Plot the ECG signal and the R peaks."""
        plots.r_plotting(self)
        plots.lorenz_plot(self)

    def r_stats(self) -> None:
        """Calculate R wave statistics."""
        # Calculate Pearson's correlation coefficient
        self.correlation_coefficient = np.corrcoef(self.rr_int[:-1], self.rr_int[1:])[0, 1]
        # BPM calculation
        self.bpm = 2 * self.r_peaks[:, 0].shape[0]

    def p_plot(self) -> None:
        """Plot the ECG signal and the P peaks."""
        plots.p_plotting(self)

