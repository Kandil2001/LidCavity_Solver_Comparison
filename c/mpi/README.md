# C MPI Case Runner

**Role:** Case-level MPI implementation  
**Language/platform:** C + MPI

This folder uses MPI to distribute independent benchmark cases across ranks. It is useful for running parameter studies faster.

## Run

```bash
make smoke NP=2
make quick NP=4
```

## Single case example

```bash
mpirun -np 4 bin/mpi_case_driver --mode quick --solver ./bin/lid_cavity_c
```

## Folder layout

| Path | Purpose |
|---|---|
| `Makefile` | Build and run commands |
| `src/lid_cavity.c` | Single translation-unit entry file |
| `src/app/` | Command-line interface |
| `src/common/` | Shared structs and utilities |
| `src/core/` | Matrix, operators, and solver loop |
| `src/post/` | Validation and CSV output |
| `postprocess/` | Plotting scripts |
| `results/` | Generated CSV, figures, scaling, and logs |
| `tools/` | MPI result merging helpers |

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
- Each rank receives independent benchmark cases and writes raw output that can be merged after the run.

For the full project overview, see the root `README.md`.
