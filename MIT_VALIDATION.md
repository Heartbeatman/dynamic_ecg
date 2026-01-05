# MIT-BIH Validation Implementation

This document tracks the implementation of MIT-BIH Arrhythmia Database support for validating R peak detection algorithms.

## MIT-BIH Database Structure

Each recording has three files:
- `.dat` - Binary signal data (2 channels, 360 Hz, 30 minutes)
- `.hea` - Header file with metadata (sample rate, gain, etc.)
- `.atr` - Annotation file with expert beat labels

---

## Implementation Tasks

### Phase 1: WFDB Loader

- [x] **1.1** Install wfdb library (add to requirements.txt) `/Users/kevindejbod/dynamic_ecg/requirements.txt`

- [x] **1.2** Create MIT-BIH loader function in `/Users/kevindejbod/dynamic_ecg/src/io/mitbih.py`
  - Read signal data using wfdb.rdrecord()
  - Read annotations using wfdb.rdann()
  - Return ECGLead objects with ground truth annotations

- [x] **1.3** Export loader in `/Users/kevindejbod/dynamic_ecg/src/io/__init__.py`

### Phase 2: Validation Metrics

- [x] **2.1** Create validation metrics in `/Users/kevindejbod/dynamic_ecg/src/analysis/validation.py`
  - Sensitivity (Se): TP / (TP + FN)
  - Positive Predictivity (+P): TP / (TP + FP)
  - F1 Score: 2 * Se * +P / (Se + +P)
  - Detection error rate

- [x] **2.2** Implement beat matching algorithm
  - Match detected peaks to annotations within tolerance window (150ms)
  - Count TP, FP, FN

### Phase 3: Validation Script

- [x] **3.1** Create validation script `/Users/kevindejbod/dynamic_ecg/examples/validate_mitbih.py`
  - Load all 48 records
  - Run detection on each
  - Calculate metrics per record and aggregate
  - Generate summary report

- [x] **3.2** Test on single record first (record 100)

---

## Progress

**Total**: 7/7 tasks complete

## Validation Results

**Aggregate Results (48 records)**:
- Total TP: 101,927 | FP: 146 | FN: 7,567
- Gross Sensitivity: 93.09%
- Gross Positive Predictivity: 99.86%
- Gross F1 Score: 0.9635
- Average Detection Error Rate: 6.54%

**Best Performing Records**:
- Record 113: Se 99.89%, +P 100.00%, F1 0.9994
- Record 230: Se 99.82%, +P 100.00%, F1 0.9991
- Record 117: Se 99.80%, +P 100.00%, F1 0.9990

**Challenging Records** (lower sensitivity due to arrhythmias/noise):
- Record 228: Se 47.35% (significant arrhythmias)
- Record 114: Se 67.64%
- Record 215: Se 74.96%
- Record 203: Se 75.97%
- Record 208: Se 76.04%

## Notes

- MIT-BIH sample rate: 360 Hz
- Annotation symbols: N (normal), V (PVC), A (APB), etc.
- Standard tolerance window: 150ms (54 samples at 360 Hz)
- Algorithm: Pan-Tompkins with adaptive thresholding and search-back
