# Implementation layout

## Canonical domain implementations

```text
src/c/
  openmp_domain_looped/
  openmp_domain_vectorized/
  mpi_domain_looped/
  mpi_domain_vectorized/
  hybrid_mpi_openmp_looped/
  hybrid_mpi_openmp_vectorized/

src/cpp/
  same six variants

src/python/
  mpi_domain_looped/
  mpi_domain_vectorized/
  hybrid_mpi_openmp_looped/
  hybrid_mpi_openmp_vectorized/
```

MPI variants divide one grid across ranks. Hybrid variants combine that spatial decomposition with threads inside each rank.

## Reference implementations

```text
matlab/
python/serial/
c/serial/
c/openmp/
cpp/serial/
cpp/openmp/
```

These belong to the earlier pressure-correction study.

## Run and result locations

- `scripts/`: local build, smoke, benchmark, and post-processing tools.
- `hpc/stromboli/`: maintained Slurm entry points.
- `results/final/`: complete archived domain performance package.
- `results/selected/`: reproducible README-facing subset.
- `comparison/figures/physics_final/`: retained pressure-correction validation figures.

Generated binaries, caches, backup files, and obsolete workflow snapshots are not tracked.
