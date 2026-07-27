# C Implementations

This folder contains the C versions of the lid-driven cavity solver.

| Folder | Purpose |
|---|---|
| `serial/` | Compiled serial CPU baseline |
| `openmp/` | Shared-memory CPU threaded version |
| `mpi/` | Case-level MPI runner for parameter studies |

All C folders follow the same structure: `README.md`, `Makefile`, `src/`, `postprocess/`, and `results/`.

## Important note about labels

The C solver is one compiled baseline. Older names such as `serial_c_looped`, `serial_c_vectorized`, `openmp_c_looped`, and `openmp_c_vectorized_style` are accepted as aliases for backward compatibility, but they are not separate C algorithms.

Use the serial version first, then compare against OpenMP and MPI.
