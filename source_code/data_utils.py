from dataclasses import dataclass
from pyedflib import highlevel
import ecg_utils as ecg
from ecg_utils import timer_decorator
import numpy as np
import concurrent.futures
import vis_utils as vis
from scipy import signal as sig
import watch_utils as watch

@dataclass
class ecg_lead:
    lead: int
    signal: np.ndarray
    fs: int
    U: str
    r_peaks: np.ndarray = None
    p_peaks: np.ndarray = None
    t_peaks: np.ndarray = None
    window: np.ndarray = None
    phasor: np.ndarray = None
    threshold: float = None
    rr_int: np.ndarray = None
    frequency_bins: np.ndarray = None
    time_bins: np.ndarray = None

    ## Stats
    bpm: float = None
    correlation_coefficient: float = None

    def __post_init__(self):
        '''
        Performs signal preprocessing and R wave detection on the ECG signal.
        '''
        self.__signal_preprocessing()
        self.r_wave_detector()
        self.p_wave_detector()
        self.calculate_rr_int()
        self.r_stats()



    def __signal_preprocessing(self):
        '''
        Performs signal preprocessing on the ECG signal.
        '''
        if self.signal.shape[0] > 1e6:
            print('Signal too long, slicing to 5 minutes')
            window_slice = int(60 * self.fs * 5)
            self.signal = self.signal[:window_slice]/1000
        else:
            print('Signal not too long, not slicing')
            self.signal = self.signal/1000
        
        if self.U == 'uV':
            self.signal = (self.signal)
    
    @timer_decorator
    def threshold_calc(self, transformed_signal):
        '''
        Function to calculate the threshold for the R peak detector
        '''

        # Calculate the mean of the transformed signal
        transformed_signal = transformed_signal[(transformed_signal > 0.01) & (transformed_signal < 2)]
        ## take the argmax of the histogram
        
        return transformed_signal.mean()/4

        

    @timer_decorator
    def r_wave_detector(self):
        """
        Function to detect the R peaks of a signal
        args:
            X: the signal
            freq: the frequency of the signal
            threshold: the threshold for the peak detector
        returns:
            rwave_array: the R peaks of the signal, giving sample position and wave-width.
        """
        ## window is the transformed signal
        self.window = ecg.grad_sqaure_conv(self.signal, self.fs, sin_wave=False)
        ## calculate the threshold
        self.threshold = self.threshold_calc(self.window)
        ## perform the peak detection on this transformed signal
        self.r_peaks = ecg.peak(X=self.window, TH=self.threshold)
        ## we filter by width to ensure we only get the R peaks
        

    @timer_decorator
    def calculate_rr_int(self):
        """
        Function to calculate the RR intervals from the R peak positions.
        """
        self.rr_int = np.diff(self.r_peaks[:,0],prepend=0)


    @timer_decorator
    def p_wave_detector(self):
        """
        Function to detect the P peaks of a signal
        args:
            X: the signal
            freq: the frequency of the signal
            threshold: the threshold for the peak detector
        returns:
            rwave_array: the R peaks of the signal, giving sample position and wave-width.
        """
        ## phasor
        self.phasor = ecg.phasor_transform(self.signal, rv=0.001)
        ## calculate the threshold
        self.threshold = self.threshold_calc(self.phasor)
        ## perform the peak detection on this transformed signal
        self.p_peaks = ecg.peak(X=self.phasor, TH=self.threshold)

    def r_plot(self):
        '''
        Function to plot the ECG signal and the R peaks
        args:
            lead_1: the lead to plot
        '''
        vis.r_plotting(self)

        vis.lorenz_plot(self)

    def r_stats(self):
        # Calculate Pearson's correlation coefficient
        self.correlation_coefficient = np.corrcoef(self.rr_int[:-1], self.rr_int[1:])[0, 1]

        ## bpm
        self.bpm = 2*self.r_peaks[:,0].shape[0]

        

@dataclass
class ecg_data:
    file_path: str
    fs: int = None
    U: str = None
    lead_1: ecg_lead = None
    lead_2: ecg_lead = None
    lead_3: ecg_lead = None
    common_beats: np.ndarray = None

    def __post_init__(self):
        '''
        Reads the ECG data from the EDF file.
        '''
        self.__read_data()

    def __read_data(self):
        '''
        Reads the ECG data from the EDF file.
        '''
        if self.file_path.endswith('.npz'):
            self.__read_npz_data()
        elif self.file_path.endswith('.EDF'):
            self.__read_edf_data()
        elif self.file_path.endswith('.csv'):
            self.__read_watch_data()


    def __read_watch_data(self):
        '''
        Reads the ECG data from the NPZ file.
        '''
        data = watch.csv_to_numpy(self.file_path)
        self.fs = data[1]
        self.U = 'uV'
        self.lead_1 = ecg_lead(signal=data[0],fs=self.fs,U=self.U,lead=0)

    def __read_npz_data(self):
        '''
        Reads the ECG data from the NPZ file.
        '''
        data = np.load(self.file_path)
        self.fs = int(data['fs'])
        self.U = 'uV'
        self.lead_1 = ecg_lead(signal=data['ecg_1'],fs=self.fs,U=self.U,lead=0)
        self.lead_2 = ecg_lead(signal=data['ecg_2'],fs=self.fs,U=self.U,lead=1)
        self.lead_3 = ecg_lead(signal=data['ecg_3'],fs=self.fs,U=self.U,lead=2)

    def __read_edf_data(self):
        signals, signal_headers, header = highlevel.read_edf(self.file_path)
        self.fs = signal_headers[0]['sample_rate']
        self.U = signal_headers[0]['dimension']

        # Process the leads in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit tasks
            futures = [executor.submit(ecg_lead, i, signals[i], self.fs, self.U) for i in range(3)]

            # Wait for all futures to complete and collect results
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Assign the results using ecg_lead.lead
        self.lead_1 = [result for result in results if result.lead == 0][0]
        self.lead_2 = [result for result in results if result.lead == 1][0]
        self.lead_3 = [result for result in results if result.lead == 2][0]

