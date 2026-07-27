# C++ Implementations

This folder contains the C++ versions of the lid-driven cavity solver.

| Folder | Purpose |
|---|---|
| `serial/` | Structured serial compiled-code baseline |
| `openmp/` | Shared-memory CPU parallel version |
| `mpi/` | Case-level MPI runner for parameter studies |

All C++ folders follow the same structure: `README.md`, `Makefile`, `src/`, `postprocess/`, and `results/`.

Use the serial C++ version as the clean compiled baseline, then compare against OpenMP and MPI.
