# C OpenMP Solver

**Role:** Shared-memory CPU implementation  
**Language/platform:** C + OpenMP

This folder adds OpenMP parallel regions to the C solver for shared-memory CPU scaling tests.

## Run

```bash
make smoke OMP_NUM_THREADS=4
make quick OMP_NUM_THREADS=4
make scaling
```

## Single case example

```bash
make run N=64 RE=100 SCHEME=central PRESSURE=RBGS OMP_NUM_THREADS=4
```

## Folder layout

| Path | Purpose |
|---|---|
| `Makefile` | Build, run, and scaling commands |
| `src/lid_cavity.c` | Single translation-unit entry file |
| `src/app/` | Command-line interface |
| `src/common/` | Shared structs and utilities |
| `src/core/` | OpenMP-enabled operators and solver loop |
| `src/post/` | Validation and CSV output |
| `postprocess/` | Plotting and scaling scripts |
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

- Use this version to compare thread scaling against the serial C baseline.

For the full project overview, see the root `README.md`.
