# MATLAB Solver

**Role in the project:** reference workflow and validation baseline.

This folder contains the MATLAB version of the lid-driven cavity solver. It is used as the clearest starting point before comparing the same benchmark with Python, C, C++, OpenMP, MPI, and CUDA.

The MATLAB code is intentionally kept readable. It contains the main solver workflow, validation against Ghia et al. centerline data, and plotting routines.

## What this folder contains

| Path | Purpose |
|---|---|
| `main.m` | Main entry point |
| `run_smoke.m` | Smallest test run |
| `run_quick.m` | Small benchmark run |
| `run_medium.m` | Larger benchmark run |
| `core/` | Numerical solver routines |
| `studies/` | Parametric-study runners and CSV export |
| `validation/` | Ghia validation data and functions |
| `post/` | Plotting functions |
| `results/` | Generated data and figures |

## Run

From this folder:

```bash
make smoke
make quick
make medium
make plots
```

The direct MATLAB commands are:

```bash
matlab -batch "run_smoke"
matlab -batch "run_quick"
matlab -batch "run_medium"
```

## Output

Generated files are written to:

```text
results/data/
results/figures/
```

Typical quick-run summary:

```text
results/data/study_summary_quick_matlab.csv
```

## Notes

- This is the reference implementation for the comparison repo.
- The code contains looped and vectorized MATLAB-style parts.
- The focus is clarity first, then comparison with faster compiled implementations.
- The output naming is slightly different from the other solvers because MATLAB summary files include `_matlab` in the file name.

## Back to main repo

The full comparison workflow is described in the root `README.md`.
