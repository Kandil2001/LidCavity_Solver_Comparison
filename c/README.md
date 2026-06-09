# C Implementations

This folder contains the C versions of the lid-driven cavity solver.

| Folder | Purpose |
|---|---|
| `serial/` | Low-level serial CPU baseline |
| `openmp/` | Shared-memory CPU parallel version |
| `mpi/` | Case-level MPI runner for parameter studies |

All C folders follow the same structure: `README.md`, `Makefile`, `src/`, `postprocess/`, and `results/`.

## Note about serial labels

The serial C folder may write two labels: `serial_c_looped` and `serial_c_vectorized`. These are benchmark labels used to keep the comparison table aligned with the MATLAB and Python studies. Both paths are still plain serial C, not SIMD/vector-intrinsics code. The true parallel C versions are kept separately in `openmp/` and `mpi/`.

Use the serial version first, then compare against OpenMP and MPI.
