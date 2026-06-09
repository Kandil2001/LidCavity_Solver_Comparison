# C++ OpenMP Solver

**Role in the project:** shared-memory CPU parallel version of the C++ solver.

This folder adds OpenMP to the C++ implementation. It is used to test how much speedup is possible when the same benchmark is run with multiple CPU threads.

## Requirements

```text
g++ with OpenMP support
make
python3 for plotting
```

Check OpenMP support:

```bash
g++ -fopenmp --version
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

- Compare results and runtime against `cpp/serial/`.
- Run several thread counts before drawing conclusions.
- Speedup depends strongly on mesh size and the number of available CPU cores.
