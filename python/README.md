# Python Implementations

This folder contains the Python versions of the lid-driven cavity solver.

| Folder | Purpose |
|---|---|
| `serial/` | Readable NumPy-based serial implementation |
| `mpi/` | Case-level MPI runner using `mpi4py` |

Both Python folders follow the same project style as the compiled versions: `README.md`, `Makefile`, `src/`, `postprocess/`, and `results/`.

The serial folder includes two comparison labels: `serial_python_vectorized` for the NumPy-style path and `serial_python_looped` for the more explicit loop-based path.

Use Python when readability and quick post-processing matter more than maximum runtime performance.
