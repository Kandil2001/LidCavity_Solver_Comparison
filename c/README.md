# C Implementations

This folder contains the C versions of the lid-driven cavity solver.

| Folder | Purpose |
|---|---|
| `serial/` | Low-level serial CPU baseline |
| `openmp/` | Shared-memory CPU parallel version |
| `mpi/` | Case-level MPI runner for parameter studies |

All C folders follow the same structure: `README.md`, `Makefile`, `src/`, `postprocess/`, and `results/`.

Use the serial version first, then compare against OpenMP and MPI.
