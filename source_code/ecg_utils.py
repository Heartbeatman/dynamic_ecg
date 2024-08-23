import numpy as np
from scipy import signal as si
import time as time
from signal_utils import butter_highpass_filter, standardise





def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time for {func.__name__}: {execution_time} seconds")
        return result
    return wrapper




@timer_decorator
def peak(signal:np.ndarray, threshold:float) -> np.ndarray:
    """
    Function to find the peaks of a signal
    Args:
        signal (np.ndarray): The signal
        threshold (float): The threshold for peak detection
    Returns:
        np.ndarray: The peaks of the signal
    """
    # Calibrate the signal by pinning a 1 to the start and end of the signal
    signal = np.concatenate((np.ones(1), signal, np.ones(1)))
    
    indices = np.flatnonzero(signal > threshold)

    differences = np.diff(indices) - 1
    
    edges = np.flatnonzero(differences) + 1
    
    window_centers = np.rint(0.5 * (edges[:, 0] + edges[:, 1])).astype(int)
    
    peaks = np.column_stack((indices[window_centers], np.diff(edges)[:, 0]))
    
    return peaks

@timer_decorator
def grad_sqaure_conv(X, freq=125, sin_wave=False) -> np.ndarray:
    """
    Function to transform the signal to find the peaks

    Args:
        X (np.ndarray): The signal
        freq (int): The frequency of the signal
        sin_wave (bool): Flag to indicate whether to create a sin wave

    Returns:
        np.ndarray: The transformed signal
    """

    ## window length is the size of the correlation sliding window,
    window_length = int(freq / 5)


    ## if sin_wave is true
    if sin_wave == True:
        ## create a sin wave
        sliding = np.sin(np.arange(0, np.pi, np.pi / window_length)) ** 2
    else:
        ## create a sliding window of ones
        sliding = np.ones(window_length)

    ## perform differentiation & squaring, as per Pan-Tompkins.
    gradient_sqaured = (np.diff(X)) ** 2
    ## perform the correlation of transformed peak signal with the sliding window
    window = si.correlate(gradient_sqaured, sliding, mode='same', method='direct')


    return window


def phasor_transform(lead,rv)->np.ndarray:
    """
    This function performs the phasor transform on the lead.
    lead: the lead to analyze (numpy array)
    rv: the reference scale (float)
    """
    phi_t  = np.arctan2((lead),(rv))
    
    return phi_t

def phrt(lead,th)->np.ndarray:
    '''
    Function to perform the phasor transform on a signal
    args:
        lead: the lead to analyze
        th: the threshold for the R peak detector
    returns:
        phi_t: the phase of the signal, as an array
    '''

    

    phi_atrial  = np.arctan((lead)/(th)) +(np.pi)/2

    phi_t = peak(signal=phi_atrial,threshold=th)

    return phi_t



def P_wave(Z,th):
    '''
    Function to find the P waves of a signal
    args:
        Z: the signal
        th: the threshold for the R peak detector
    returns:
        Pwaves: the P waves of the signal, giving sample position and wave-width.
    '''

    X = phasor_transform(Z,th)
    Pwaves = filter_by_width(X,5,30)
    return Pwaves


def PR(Z,Y):
    

    H = P_wave(Z,0.30)


    Join = np.concatenate((Y, H), axis=-0)
    
    big_sort = lambda L: L[np.lexsort((L[:,1],L[:,0]))]
    
    F = (abs(np.diff(big_sort(Join),axis=0)))

    F = F[F[:,0]>5]
    F = F[F[:,1]>2]
    F = F[F[:,0]<30]

    unique, counts = np.unique((F[:,0]), return_counts=True)
    Q = (np.asarray((counts, unique)).T)
    

    PR_t = lambda a: np.average((a[-3:-1,1]),weights=(a[-3:-1,0]))

    
    return PR_t(big_sort(Q))


def filter_by_width(beat_array,lower,upper)->np.ndarray:
    '''
    This function takes in the R beats and filters them by size (column 1), and returns the array of filtered Rwaves
    args:
        r_array: numpy array of R beats
        lower: lower bound for size
        upper: upper bound for size
    returns:
        r_array: numpy array of R beats filtered by size
    '''

    beat_array = beat_array[(beat_array[:,1]>lower) & (beat_array[:,1]<upper)]

    return beat_array
