# Dynamic ECG Refactoring TODO

This document tracks the refactoring tasks for reorganising the Dynamic ECG codebase.

## Status Key
- ✅ Complete
- 🚧 In Progress
- ❌ Not Started

## Tasks

### 1. Project Structure ✅
- [x] Create new branch: `refactor/reorganise-structure`
- [x] Update .gitignore with Claude-related entries
- [x] Reorganise data files into csv/edf/npz directories
- [x] Create data format documentation
- [x] Create Apple Watch export guide
- [x] Reorganise source code (remove utils pattern)
- [x] Move images to docs/images structure
- [x] Archive old utils files to .archive/

### 2. Data Organisation ✅
#### Directory Structure:
```
data/
├── csv/
│   ├── apple_watch/
│   └── holter/
├── edf/
├── npz/
└── README.md
```

### 3. Source Code Reorganisation ✅
#### New Structure:
```
src/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── ecg_lead.py
│   └── ecg_data.py
├── io/
│   ├── __init__.py
│   ├── loaders.py
│   └── apple_watch.py
├── processing/
│   ├── __init__.py
│   ├── filters.py
│   ├── detectors.py
│   └── transforms.py
├── visualisation/
│   ├── __init__.py
│   └── plots.py
└── analysis/
    ├── __init__.py
    └── metrics.py
```

### 4. Waveform Detection TODOs ❌

#### Current Status:
- ✅ R peak detection (QRS complex) - Working
- 🚧 P wave detection - Has dimensionality issues
- ❌ T wave detection - Not implemented

#### Detection Tasks:
1. **Fix P Wave Detection**
   - [ ] Fix 1D vs 2D array issue
   - [ ] Implement proper width filtering
   - [ ] Validate detection accuracy

2. **Implement T Wave Detection**
   - [ ] Research T wave characteristics
   - [ ] Design detection algorithm
   - [ ] Add visualisation support

3. **PQRST Analysis**
   - [ ] PR interval calculation
   - [ ] QT interval measurement
   - [ ] ST segment analysis

4. **Advanced Detection**
   - [ ] QRS morphology classification
   - [ ] Atrial fibrillation detection
   - [ ] Premature beat detection
   - [ ] Bundle branch block detection

5. **Testing & Validation**
   - [ ] Unit tests for all detectors
   - [ ] MIT-BIH database validation
   - [ ] Performance benchmarking

### 5. Documentation Updates ❌
- [ ] Update README.md with new structure
- [ ] Create API documentation
- [ ] Add example notebooks for each feature
- [ ] Document algorithm implementations

### 6. Testing ❌
- [ ] Set up pytest framework
- [ ] Write unit tests for core modules
- [ ] Integration tests for file loading
- [ ] Performance tests for detectors

## Notes
- All file paths to use Australian English spelling
- Remove adjectives and maintain engineering tone
- Ensure venv and .venv are in .gitignore
- Use CLAUDE.md for commit guidance