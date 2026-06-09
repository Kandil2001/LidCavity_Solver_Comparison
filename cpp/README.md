# C++ Implementations

This folder contains the C++ versions of the lid-driven cavity benchmark.

The C++ implementation is the structured compiled-code baseline. It keeps the code cleaner than the plain C version while still giving compiled performance.

## Folders

| Folder | Purpose |
|---|---|
| `serial/` | Serial C++ CPU solver |
| `openmp/` | C++ solver with OpenMP parallelism |
| `mpi/` | C++ MPI runner for independent benchmark cases |

## Recommended order

```bash
cd serial
make smoke
make quick
```

Then test OpenMP:

```bash
cd ../openmp
make smoke OMP_NUM_THREADS=4
make quick OMP_NUM_THREADS=4
```

Use MPI only on a machine with `mpicc` and `mpirun`:

```bash
cd ../mpi
make smoke NP=2
make quick NP=4
```

## Notes

- `serial/` is the clean C++ baseline.
- `openmp/` is for shared-memory CPU scaling.
- `mpi/` is currently case-parallel, not domain decomposition.
