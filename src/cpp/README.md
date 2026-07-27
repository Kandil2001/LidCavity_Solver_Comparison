# C++ Implementations

This folder contains the C++ versions of the lid-driven cavity solver.

| Folder | Purpose |
|---|---|
| `serial/` | Structured serial compiled-code baseline |
| `openmp/` | Shared-memory CPU parallel version |
| `mpi/` | Case-level MPI runner for parameter studies |
| `hybrid_mpi_openmp/` | True row-wise MPI domain decomposition with OpenMP threading |

All C++ folders follow the same structure: `README.md`, `Makefile`, `src/`, `postprocess/`, and `results/`.

Use the serial C++ version as the clean compiled baseline. Use `openmp/` for shared-memory loop parallelism, `mpi/` for case-level parameter sweeps, and `hybrid_mpi_openmp/` for the actual MPI domain-decomposition solver.
