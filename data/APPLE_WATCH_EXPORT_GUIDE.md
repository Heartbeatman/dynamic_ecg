# Apple Watch ECG Export Guide

This guide explains how to export ECG data from your Apple Watch to use with Dynamic ECG.

## Requirements
- Apple Watch Series 4 or later
- iPhone with Health app
- ECG recordings in Health app

## Export Steps

### 1. Open Health App
Open the Health app on your iPhone.

### 2. Navigate to ECG Data
1. Tap the **Browse** tab at the bottom
2. Select **Heart**
3. Tap **Electrocardiograms (ECG)**

### 3. View ECG Recording
1. Select the ECG recording you want to export
2. You'll see the ECG waveform and details

### 4. Export Single ECG
1. While viewing the ECG, tap **Export a PDF for your doctor**
2. Instead of PDF, scroll down and tap **Export as CSV**
3. Choose where to save or share the file

### 5. Bulk Export (All Health Data)
For multiple ECG recordings:
1. In Health app, tap your profile picture (top right)
2. Scroll down and tap **Export All Health Data**
3. Tap **Export**
4. This creates a zip file containing all health data
5. Extract the zip and find ECG files in:
   ```
   export/electrocardiograms/
   ```

## File Format
Apple Watch ECG CSV files have this structure:
- Header rows with metadata (device info, sampling rate)
- Voltage samples starting from row 10
- Single lead (Lead I) data
- 512 Hz sampling rate

## Using with Dynamic ECG
```python
import data_utils as data

# Load Apple Watch ECG
ecg = data.ecg_data('data/csv/apple_watch/ecg_2021-12-17.csv')

# View R peaks
ecg.lead_1.r_plot()
```

## Tips
- ECG recordings are typically 30 seconds long
- Files are named with the recording date
- Ensure good skin contact for quality recordings
- Keep still during recording to reduce noise