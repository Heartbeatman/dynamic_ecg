"""
Wave detection algorithms.

This module re-exports functions from peak.py and adaptive.py
for backwards compatibility.
"""
from .peak import peak, peak_core, filter_by_width
from .utils import timer_decorator
from .adaptive import (
    adaptive_peak_detect,
    calculate_adaptive_threshold,
    update_signal_peak_estimate,
    update_noise_peak_estimate,
    init_thresholds_from_training,
    get_candidate_peaks,
    search_back_for_missed_peak,
    classify_peaks,
)

__all__ = [
    # Simple detection
    'peak',
    'peak_core',
    'filter_by_width',
    'timer_decorator',
    # Adaptive detection
    'adaptive_peak_detect',
    'calculate_adaptive_threshold',
    'update_signal_peak_estimate',
    'update_noise_peak_estimate',
    'init_thresholds_from_training',
    'get_candidate_peaks',
    'search_back_for_missed_peak',
    'classify_peaks',
]
