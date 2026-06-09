# C++ Serial Solver

**Role in the project:** structured compiled-code baseline.

This folder contains the serial C++ implementation of the lid-driven cavity solver. It is intended to be readable, modular, and faster than the MATLAB/Python reference versions for larger cases.

## What this folder contains

| Path | Purpose |
|---|---|
| `src/lid_cavity.cpp` | Main build target |
| `src/core/` | Solver and numerical operators |
| `src/common/` | Shared helper routines |
| `src/app/` | Command-line handling |
| `src/post/` | Validation and output routines |
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
./bin/lid_cavity --single --N 128 --Re 400 --scheme upwind --pressure RBGS
```

## Output

```text
results/data/      CSV summaries, fields, residuals
results/figures/   generated plots
```

## Notes

- This is the main compiled-code baseline.
- Use it as the reference before testing C++ OpenMP or C++ MPI.
- It is also useful for comparing against the separate `LidCavity_CPP` repository.
