import sys
import os
# Add parent directory to path to import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import ECGData
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Load Holter data
Holter = ECGData('data/edf/9ef19ac2-a4f6-4c95-9aaf-c709ed7cd958-edf-20240112041135.edf')

# Plot R peaks for lead 2
Holter.lead_2.r_plot()