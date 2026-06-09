# C OpenMP Solver

**Role in the project:** shared-memory CPU parallel version of the C solver.

This folder adds OpenMP to the C implementation. It is used to compare the serial C baseline with a multi-threaded CPU version on the same machine.

## Requirements

```text
gcc with OpenMP support
make
python3 for plotting
```

Check OpenMP support:

```bash
gcc -fopenmp --version
```

## Build and run

```bash
make build
make smoke OMP_NUM_THREADS=4
make quick OMP_NUM_THREADS=4
make run N=128 RE=400 SCHEME=upwind PRESSURE=RBGS OMP_NUM_THREADS=4
```

## Scaling check

```bash
make scaling
make plot
```

Scaling output:

```text
results/scaling/openmp_scaling.csv
```

## Notes

- This is shared-memory parallelism, so it runs on one node or one workstation.
- Try thread counts such as 1, 2, 4, 8, 16 depending on the machine.
- Compare against `c/serial/` before interpreting speedup.
