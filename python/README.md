# Python Implementations

This folder contains the Python versions of the lid-driven cavity benchmark.

Python is used here for two reasons: readability and easy post-processing. It is not expected to be the fastest implementation, but it is very useful for checking the numerical workflow and handling CSV/plotting scripts.

## Folders

| Folder | Purpose |
|---|---|
| `serial/` | Readable NumPy-based serial solver |
| `mpi/` | MPI runner for distributing independent benchmark cases |

## Recommended order

Start with the serial version:

```bash
cd serial
make install
make smoke
make quick
```

Then use MPI only if `mpirun` and `mpi4py` are available:

```bash
cd ../mpi
make install
make smoke NP=2
make quick NP=4
```

## Notes

- The serial version is best for understanding and debugging.
- The MPI version is case-parallel, not domain decomposition.
- Generated outputs stay inside each subfolder under `results/`.
