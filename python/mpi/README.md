# Python MPI runner

This folder runs independent benchmark cases in parallel using MPI. It is case-level parallelism, not domain decomposition.

## Requirements

You need `mpirun` and `mpi4py`.

```bash
make install
```

## Run

```bash
make smoke NP=2
make quick NP=4
```

The output files are merged under `results/data/`.
