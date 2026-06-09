# Python Serial Solver

**Role in the project:** readable serial implementation and post-processing-friendly baseline.

This folder contains the Python / NumPy version of the lid-driven cavity solver. It is easier to read than the C and C++ versions and is useful for checking the numerical workflow before moving to faster compiled code.

## What this folder contains

| Path | Purpose |
|---|---|
| `src/lid_cavity.py` | Main launcher |
| `src/lidcavity/` | Solver package |
| `postprocess/` | Plotting scripts |
| `requirements.txt` | Python dependencies |
| `results/` | Generated data and plots |

## Setup

```bash
make install
```

or manually:

```bash
python3 -m pip install -r requirements.txt
```

## Run

```bash
make smoke
make quick
make run N=128 RE=400 SCHEME=upwind PRESSURE=RBGS
make plot
```

Direct command example:

```bash
python3 src/lid_cavity.py --single --N 128 --Re 400 --scheme upwind --pressure RBGS
```

## Output

```text
results/data/      CSV summaries, fields, residuals
results/figures/   generated plots
```

Typical summary file:

```text
results/data/study_summary_quick.csv
```

## Notes

- Good first folder for checking the algorithm in a readable language.
- Slower than C/C++ for larger cases, but easier to debug.
- Output files are designed to be compared with the other implementations.
