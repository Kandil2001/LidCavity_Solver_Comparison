# MATLAB Reference Solver

**Role:** Reference workflow  
**Language/platform:** MATLAB

This folder contains the reference MATLAB implementation. It keeps the numerical workflow easy to read and is useful for checking the other implementations.

## Run

```bash
make smoke
make quick
make medium
```

## Single case example

```bash
matlab -batch "run_mode('quick')"
```

## Folder layout

| Path | Purpose |
|---|---|
| `Makefile` | Common MATLAB run commands |
| `run_smoke.m / run_quick.m / run_medium.m` | Mode entry scripts |
| `src/core/` | Numerical operators and SIMPLE loop |
| `src/studies/` | Single-case and parametric-study drivers |
| `src/validation/` | Ghia centerline validation data and checks |
| `src/postprocess/` | MATLAB plotting functions |
| `postprocess/` | README and post-processing note |
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

- This is the easiest implementation to follow when checking the numerical method.
- The folder is now organised with a `src/` tree like the other implementations.

For the full project overview, see the root `README.md`.
