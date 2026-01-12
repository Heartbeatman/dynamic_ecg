# Beat Type Detection Analysis

This document provides a detailed breakdown of R-peak detection performance by beat type on the MIT-BIH Arrhythmia Database.

---

## Overview

The MIT-BIH Arrhythmia Database contains expert-annotated beat classifications, allowing us to analyse detection performance across different cardiac rhythm types. This analysis identifies specific weaknesses in the Pan-Tompkins detector and informs targeted improvements.

**Database**: MIT-BIH Arrhythmia Database (48 records, 109,494 annotated beats)

**Algorithm**: Pan-Tompkins with adaptive thresholding and two-pass detection

---

## Results by Individual Beat Type

| Symbol | Beat Type | Total Beats | TP | FN | Sensitivity |
|--------|-----------|-------------|----|----|-------------|
| N | Normal | 75,052 | 73,023 | 2,029 | 97.30% |
| L | Left bundle branch block | 8,075 | 8,040 | 35 | 99.57% |
| R | Right bundle branch block | 7,259 | 7,234 | 25 | 99.66% |
| V | Premature ventricular contraction | 7,130 | 6,304 | 826 | **88.42%** |
| / | Paced beat | 7,028 | 7,004 | 24 | 99.66% |
| A | Atrial premature beat | 2,546 | 2,385 | 161 | 93.68% |
| f | Fusion of paced and normal | 982 | 924 | 58 | 94.09% |
| F | Fusion (ventricular and normal) | 803 | 785 | 18 | 97.76% |
| j | Junctional escape beat | 229 | 227 | 2 | 99.13% |
| a | Aberrated atrial premature beat | 150 | 61 | 89 | **40.67%** |
| E | Ventricular escape beat | 106 | 105 | 1 | 99.06% |
| J | Junctional premature beat | 83 | 81 | 2 | 97.59% |
| Q | Unclassifiable beat | 33 | 28 | 5 | 84.85% |
| e | Atrial escape beat | 16 | 16 | 0 | 100.00% |
| S | Supraventricular premature beat | 2 | 2 | 0 | 100.00% |

**Total**: 109,494 beats | 106,219 TP | 3,275 FN | 97.01% Sensitivity

**False Positives**: 180 (phantom detections)

**Positive Predictivity**: 99.83%

---

## Results by Clinical Category

| Category | Total Beats | TP | FN | Sensitivity |
|----------|-------------|----|----|-------------|
| Normal | 75,052 | 73,023 | 2,029 | 97.30% |
| Bundle Branch Block (L, R, B) | 15,334 | 15,274 | 60 | **99.61%** |
| Paced (/) | 7,028 | 7,004 | 24 | **99.66%** |
| Escape (e, j, n, E) | 351 | 348 | 3 | 99.15% |
| Fusion (F, f) | 1,785 | 1,709 | 76 | 95.74% |
| Supraventricular (A, a, J, S) | 2,781 | 2,529 | 252 | 90.94% |
| Ventricular (V, r) | 7,130 | 6,304 | 826 | **88.42%** |
| Unknown (Q, ?) | 33 | 28 | 5 | 84.85% |

---

## False Negative Distribution

The 3,275 missed beats break down as follows:

| Beat Type | False Negatives | % of Total FN | Notes |
|-----------|-----------------|---------------|-------|
| Normal (N) | 2,029 | 62.0% | Large sample size; still 97.3% detected |
| PVC (V) | 826 | 25.2% | **Primary weakness** |
| APB (A) | 161 | 4.9% | Moderate concern |
| Aberrated APB (a) | 89 | 2.7% | Very poor detection rate |
| Paced fusion (f) | 58 | 1.8% | Acceptable |
| LBBB (L) | 35 | 1.1% | Excellent despite morphology |
| RBBB (R) | 25 | 0.8% | Excellent |
| Paced (/) | 24 | 0.7% | Excellent |
| Fusion (F) | 18 | 0.5% | Good |
| Other | 10 | 0.3% | Minor |

---

## Problem Areas

### 1. Premature Ventricular Contractions (PVCs) - 88.42% Sensitivity

**Impact**: 826 false negatives (25% of all missed beats)

**Root Cause Analysis**:
- PVCs have wider, often lower-amplitude QRS complexes
- Different morphology from preceding normal beats
- May fall below adaptive threshold tuned to normal rhythm
- Compensatory pause after PVC can disrupt threshold adaptation

**Affected Records**:
- Record 228: 362 PVCs, 62.9% overall sensitivity
- Record 201: Ventricular ectopy, 86.0% sensitivity
- Record 203: Multiform PVCs, 88.2% sensitivity

### 2. Aberrated Atrial Premature Beats - 40.67% Sensitivity

**Impact**: 89 false negatives (small sample of 150 total)

**Root Cause Analysis**:
- Arise from atrial ectopy but conduct aberrantly
- QRS morphology significantly different from normal
- Often wider and lower amplitude than normal beats
- Occurs infrequently, providing few training examples

**Clinical Note**: While the sample size is small (150 beats), the 40.67% detection rate is concerning for clinical applications.

### 3. Atrial Premature Beats (APBs) - 93.68% Sensitivity

**Impact**: 161 false negatives

**Root Cause Analysis**:
- Premature timing can disrupt adaptive threshold
- May occur during refractory period calculation
- Search-back mechanism may not trigger appropriately

---

## Problematic Records

| Record | Sensitivity | PPV | F1 Score | Primary Issue |
|--------|-------------|-----|----------|---------------|
| 228 | 62.9% | 99.77% | 0.7724 | Significant ventricular arrhythmias (362 PVCs) |
| 114 | 73.8% | 99.64% | 0.8477 | Atrial fibrillation, irregular rhythm |
| 201 | 86.0% | 99.29% | 0.9216 | Ventricular ectopy |
| 203 | 88.2% | 99.73% | 0.9361 | Multiform PVCs |

---

## Strengths

1. **Excellent performance on conduction abnormalities**: Bundle branch blocks (99.6%) and paced beats (99.7%) are detected very reliably despite their altered QRS morphology.

2. **Very low false positive rate**: Only 180 false positives across 109,494 beats (99.83% PPV) means very few false alarms.

3. **Strong normal rhythm performance**: 97.30% sensitivity on the largest beat category (75,052 normal beats).

4. **Two-pass detection effective**: Search-back mechanism recovers beats missed during initial training period.

---

## Recommendations for Improvement

### High Priority

1. **PVC-specific detection pass**: Add a second detection pass with parameters tuned for wider, lower-amplitude complexes.

2. **Morphology template matching**: Build templates of different beat types and match against detected complexes.

3. **Adaptive threshold adjustment**: Lower threshold temporarily after detecting irregular RR intervals.

### Medium Priority

4. **Aberrated APB handling**: Add specific detection for beats with abnormal morphology but atrial origin.

5. **Multi-lead fusion**: Use second channel (V1) to improve detection of beats with unusual morphology in MLII.

### Future Work

6. **Machine learning classifier**: Train CNN or transformer model on beat morphologies for improved classification.

7. **Real-time adaptation**: Implement online learning to adapt to patient-specific morphologies.

---

## Methodology

**Validation Script**: `examples/validate_beat_types.py`

**Tolerance Window**: 150ms (54 samples at 360 Hz)

**Beat Symbols Included**: N, L, R, B, A, a, J, S, V, r, F, e, j, n, E, /, f, Q, ?

**Processing Pipeline**:
1. Load MIT-BIH record using wfdb library
2. Apply highpass filter to remove baseline wander
3. Run Pan-Tompkins R-peak detection with adaptive thresholding
4. Match detected peaks to ground truth within tolerance window
5. Track true positives and false negatives by beat type

---

*Analysis generated: January 2026*
*Algorithm version: MIT-validation branch*
