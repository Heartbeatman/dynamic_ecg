"""Signal processing functions."""
from .filters import butter_bandpass_filter, butter_highpass_filter, standardise
from .transforms import grad_square_conv, phasor_transform
from .peak import peak, peak_core, filter_by_width
from .adaptive import adaptive_peak_detect
from .utils import timer_decorator

__all__ = [
    # Filters
    'butter_bandpass_filter', 'butter_highpass_filter', 'standardise',
    # Transforms
    'grad_square_conv', 'phasor_transform',
    # Peak detection
    'peak', 'peak_core', 'filter_by_width',
    'adaptive_peak_detect',
    # Utils
    'timer_decorator',
]