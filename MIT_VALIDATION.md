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
- Total TP: 106,219 | FP: 180 | FN: 3,275
- Gross Sensitivity: 97.01%
- Gross Positive Predictivity: 99.83%
- Gross F1 Score: 0.9840
- Average Detection Error Rate: 3.28%

**Best Performing Records**:
- Record 122: Se 100.0%, +P 100.00%, F1 1.0000
- Record 115: Se 99.90%, +P 100.00%, F1 0.9995
- Record 103: Se 99.86%, +P 100.00%, F1 0.9993

**Challenging Records** (lower sensitivity due to arrhythmias):
- Record 228: Se 62.9% (362 PVCs)
- Record 114: Se 73.8% (atrial fibrillation)
- Record 201: Se 86.0% (ventricular ectopy)
- Record 203: Se 88.2% (multiform PVCs)

**Performance by Beat Type**:
- Normal (N): 97.30% sensitivity (75,052 beats)
- Bundle Branch Block (L, R): 99.6% sensitivity (15,334 beats)
- Paced (/): 99.66% sensitivity (7,028 beats)
- PVC (V): 88.42% sensitivity (7,130 beats) - main weakness
- APB (A): 93.68% sensitivity (2,546 beats)

## Notes

- MIT-BIH sample rate: 360 Hz
- Annotation symbols: N (normal), V (PVC), A (APB), etc.
- Standard tolerance window: 150ms (54 samples at 360 Hz)
- Algorithm: Pan-Tompkins with adaptive thresholding and search-back
