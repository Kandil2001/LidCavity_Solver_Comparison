# Python MPI Case Runner

**Role:** Case-level MPI implementation  
**Language/platform:** Python / mpi4py

This folder runs independent benchmark cases across MPI ranks using the same Python solver logic.

## Run

```bash
make smoke NP=2
make quick NP=4
```

## Single case example

```bash
mpirun -np 4 python3 src/mpi_case_driver.py --mode quick --no-fields
```

## Folder layout

| Path | Purpose |
|---|---|
| `Makefile` | MPI run commands |
| `src/mpi_case_driver.py` | MPI case scheduler |
| `src/lidcavity/` | Shared solver package |
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

- This is case-level parallelism, not domain decomposition.

For the full project overview, see the root `README.md`.
