# C Implementations

This folder contains the C versions of the lid-driven cavity benchmark.

The C implementations are useful as low-level CPU baselines. They show the same numerical idea with explicit loops, explicit memory layout, and simple build commands.

## Folders

| Folder | Purpose |
|---|---|
| `serial/` | Plain C serial CPU solver |
| `openmp/` | C solver with shared-memory OpenMP parallelism |
| `mpi/` | C MPI runner for independent benchmark cases |

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

- `serial/` is the baseline.
- `openmp/` is for shared-memory CPU scaling.
- `mpi/` is currently case-parallel, not domain decomposition.
