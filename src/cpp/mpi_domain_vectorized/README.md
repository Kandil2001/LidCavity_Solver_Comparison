# cpp_mpi_domain_vectorized

This folder contains the **CPP pure MPI domain decomposition** lid-driven-cavity solver using **SIMD/vectorization-friendly local kernels**.

It solves one CFD domain split row-wise across MPI ranks. Each rank owns a block of rows and exchanges ghost rows with neighbouring ranks.

Numerical formulation: streamfunction-vorticity lid-driven cavity on a uniform grid.

## Run

```bash
make smoke NP=2
make run NP=4 N=64 RE=100 STEPS=1000 POISSON_ITERS=200 SCHEME=upwind
```

For hybrid folders, set threads per rank:

```bash
make run NP=4 OMP_NUM_THREADS=2 N=64 RE=100 STEPS=1000 POISSON_ITERS=200
```

## Output

Summary CSV files are written to:

```text
results/data/
```

Implementation label:

```text
cpp_mpi_domain_vectorized
```
