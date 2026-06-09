# C++ Serial Solver

**Role:** Compiled serial CPU implementation  
**Language/platform:** C++

This folder contains the structured serial C++ implementation. It is the main compiled-code baseline.

## Run

```bash
make smoke
make quick
```

## Single case example

```bash
make run N=64 RE=100 SCHEME=central PRESSURE=RBGS
```

## Folder layout

| Path | Purpose |
|---|---|
| `Makefile` | Build and run commands |
| `src/lid_cavity.cpp` | Single translation-unit entry file |
| `src/app/` | Command-line interface |
| `src/common/` | Shared structs and utilities |
| `src/core/` | Operators and solver loop |
| `src/post/` | Validation and CSV output |
| `postprocess/` | Plotting scripts |
| `results/` | Generated CSV, figures, scaling, and logs |

## Output

Generated files follow the same convention used across the repository:

```text
results/data/      CSV field data, residual histories, and summary tables
results/figures/   generated plots
results/scaling/   OpenMP, MPI, or CUDA scaling files when available
results/logs/      optional run logs
```


## Notes

- This is usually the cleanest compiled implementation to show first.

For the full project overview, see the root `README.md`.
