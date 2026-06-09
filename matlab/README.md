# MATLAB Reference Solver

**Role:** Reference workflow  
**Language/platform:** MATLAB

This folder contains the MATLAB reference implementation. It keeps the numerical workflow easy to inspect and is useful for checking the other implementations.

## Run

```bash
make smoke
make quick
make medium
```

## Single case example

```bash
make single
```

## Folder layout

| Path | Purpose |
|---|---|
| `Makefile` | MATLAB run commands |
| `src/app/` | Entry scripts and configuration |
| `src/core/` | Numerical operators and SIMPLE loop |
| `src/studies/` | Single-case and parametric-study drivers |
| `src/validation/` | Ghia centerline validation data and checks |
| `postprocess/` | MATLAB plotting functions |
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

- MATLAB is the reference workflow. It contains both looped and vectorized study options.
- The source now lives only under `src/`, so the folder is not duplicated.

For the full project overview, see the root `README.md`.
