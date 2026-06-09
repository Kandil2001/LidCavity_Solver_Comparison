# C Serial Solver

**Role in the project:** low-level serial CPU baseline.

This folder contains the plain C implementation of the lid-driven cavity solver. It keeps the same benchmark setup as the MATLAB, Python, and C++ versions, but uses explicit loops and manual memory handling.

## What this folder contains

| Path | Purpose |
|---|---|
| `src/lid_cavity.c` | Main single-file build target |
| `src/core/` | Solver and operator routines |
| `src/common/` | Shared helper routines |
| `src/app/` | Command-line handling |
| `src/post/` | Validation and CSV output |
| `postprocess/` | Plotting scripts |
| `results/` | Generated outputs |

## Build and run

```bash
make build
make smoke
make quick
make run N=128 RE=400 SCHEME=upwind PRESSURE=RBGS
make plot
```

Direct command example:

```bash
./bin/lid_cavity_c --single --N 128 --Re 400 --scheme upwind --pressure RBGS
```

## Output

```text
results/data/      CSV summaries, fields, residuals
results/figures/   generated plots
```

## Notes

- This is the C baseline used for runtime comparison.
- It is useful for checking the cost of moving from Python/MATLAB to compiled C.
- OpenMP and MPI versions are kept in separate folders to keep this baseline clean.
