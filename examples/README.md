# Examples

This directory contains example code demonstrating how to use the Dynamic ECG library.

## Directory Structure

```
examples/
├── notebooks/          # Jupyter notebook tutorials
│   ├── Apple_watch.ipynb   - Processing Apple Watch ECG exports
│   └── Holter.ipynb        - Processing Holter monitor data
│
├── scripts/            # Standalone Python examples
│   ├── compare_detectors.py    - Compare different detection methods
│   └── peak_detection.py       - Basic R-peak detection example
│
└── internal/           # Internal testing scripts (not distributed)
    ├── validation/     - MIT-BIH and QT database validation
    ├── testing/        - P-wave algorithm testing
    ├── plotting/       - Validation result visualisation
    └── output/         - Generated plots and animations
```

## Getting Started

### Jupyter Notebooks

The notebooks provide interactive tutorials:

```bash
cd examples/notebooks
jupyter notebook Apple_watch.ipynb
```

### Python Scripts

Run the example scripts directly:

```bash
python examples/scripts/peak_detection.py
```

## Notes

- The `internal/` directory contains development and validation scripts
- These are not intended for end users and are excluded from distribution
- See `docs/VALIDATION_REPORT.md` for algorithm validation results
