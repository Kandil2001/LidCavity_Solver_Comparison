# C MPI runner

This folder uses MPI to distribute independent benchmark cases across processes.

It is useful for running many cases faster, but it is not a domain-decomposition CFD solver yet.

## Requirements

You need `mpicc` and `mpirun`.

## Build and run

```bash
make build
make smoke NP=2
make quick NP=4
make merge
```

Merged outputs are written to `results/data/`.
