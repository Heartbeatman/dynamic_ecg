import sys

import numpy as np
from numpy._core.numerictypes import uint16

sys.path.append("..")

import matplotlib.pyplot as plt

from src.core import ECGData
from src.processing.transforms import grad_square_conv

signal_data = ECGData(
    file_path="../data/csv/holter/good_Dry_data.csv"
)

raw_signal = signal_data.lead_2.signal[120000:121000] / 2000

## okay so this is the transform of the function!
X = grad_square_conv(raw_signal, freq=signal_data.lead_2.fs)

threshold = 0.2
## now for the peak detection, let's do step by step, so first we padd the signal withones on both sides
padded_signal = np.concatenate((np.ones(1), X, np.ones(1)))

## okay now is where we start getting some time indexes. all we are doing is finding where the signal is greater then a given threshold, i.e taller then a line
points = np.flatnonzero(padded_signal > threshold)

## now we find the difference in our points, (SPOLIER we are searching for our edges. how does this work? well if we have to points DIRECTLY next to each other then our wave is still continuing. i.e if we have recorded 2,3,4,5 our wave form is still going. but if we notice a large value, that means there's a big difference.(larger diff between these two poitns)
diff_points_raw = np.diff(points).astype(uint16)
np.savetxt("Raw Difference Points.txt", np.round(diff_points_raw, 0))
diff_points = np.diff(points) - 1
np.savetxt("Difference Points.txt", np.round(diff_points, 0))

## okay nice, now we remove 1, as we want to ignore our sidebyside points we are searching for the edges.
## so, we can use a familar function, old flatnonzero - the function that returns the index of somethething that is true, and we exclude zeros.

edge_index = np.flatnonzero(diff_points)

##TODO, figure out why you add 1, i legit forgot haha + 1 

peak_blocks = np.column_stack((edge_index[:-1], edge_index[1:]))

## now we find the midpoiint of these peaks!
peak_midpoint_indexes = np.rint(0.5 * (peak_blocks[:, 0] + peak_blocks[:, 1])).astype(
    int
)

### now we get out actual peak index, by translateing all the way back to th time domain

peak_index_t = points[peak_midpoint_indexes]

wave_width = np.diff(peak_blocks[:, 0])

phasor = np.arctan2((raw_signal),(0.0002))
##
## plotting
plt.figure(figsize=(15, 10))
plt.scatter(
    peak_index_t,
    raw_signal[peak_index_t],
    label=r"$\text{Peaks}$",
    c="orange",
    marker="x",
)
plt.scatter(
    points,
    padded_signal[points],
    label=r"$\text{Points above Thresdhold}$",
    c="navy",
    alpha=0.1,
)
plt.plot(raw_signal, label=r"$\text{Lead II Raw}$", c="black")
plt.plot(X, label=r"$\text{Transformed Signal}$", c="blue")
plt.plot(phasor, label=r"$\text{Phasor Signal}$", c="green")
plt.plot(
    np.arange(0, len(raw_signal), 1),
    threshold * np.ones(len(raw_signal)),
    label=r"$\text{Threshold}$",
    c="red",
)
plt.xlabel("Samples")
plt.ylabel("Voltage mV")
plt.legend()
plt.savefig("sample.png")
plt.clf()
