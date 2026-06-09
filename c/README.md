# C Implementations

This folder contains the C versions of the lid-driven cavity solver.

| Folder | Purpose |
|---|---|
| `serial/` | Low-level serial CPU baseline |
| `openmp/` | Shared-memory CPU parallel version |
| `mpi/` | Case-level MPI runner for parameter studies |

All C folders use the same basic style: `Makefile`, `src/`, `postprocess/`, and `results/`.
