# C OpenMP solver

This version adds shared-memory CPU parallelism to the C solver using OpenMP.

Use it to compare the serial C baseline with different thread counts.

## Build and run

```bash
make build
make smoke OMP_NUM_THREADS=4
make quick OMP_NUM_THREADS=4
make run N=128 RE=400 OMP_NUM_THREADS=4
```

## Scaling check

```bash
make scaling
make plot
```

Scaling CSV files are written to `results/scaling/`.
