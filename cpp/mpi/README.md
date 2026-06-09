# C++ MPI Case Runner

**Role:** Case-level MPI implementation  
**Language/platform:** C++ + MPI

This folder runs independent C++ benchmark cases across MPI ranks.

## Run

```bash
make smoke NP=2
make quick NP=4
```

## Single case example

```bash
mpirun -np 4 bin/mpi_case_driver --mode quick --solver ./bin/lid_cavity
```

## Folder layout

| Path | Purpose |
|---|---|
| `Makefile` | Build, run, and merge commands |
| `src/lid_cavity.cpp` | Serial C++ solver binary source |
| `src/mpi_case_driver.c` | MPI case scheduler |
| `src/app/` | Command-line interface |
| `src/common/` | Shared structs and utilities |
| `src/core/` | Operators and solver loop |
| `src/post/` | Validation and CSV output |
| `tools/` | MPI result merging utilities |
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
