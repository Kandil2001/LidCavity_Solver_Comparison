# c_openmp_domain_vectorized

This folder contains the **C OpenMP-only domain solver** for the lid-driven cavity problem.

It is the shared-memory OpenMP counterpart to the MPI-domain and hybrid MPI+OpenMP domain-decomposition solvers.

## Kernel style

```text
SIMD/vectorization-friendly OpenMP local kernels
```

## Run

```bash
make smoke OMP_NUM_THREADS=2
make run OMP_NUM_THREADS=8 N=128 RE=1000 STEPS=4000 POISSON_ITERS=300 SCHEME=upwind
```

## Output

```text
results/data/c_openmp_domain_vectorized_summary.csv
```

## Scope

This is OpenMP-only scaling on one shared-memory domain. It does not split the domain across MPI ranks.
