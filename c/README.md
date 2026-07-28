# C implementations

- `serial/` and `openmp/`: earlier pressure-correction reference implementations.
- `../src/c/openmp_domain_*`: canonical streamfunction–vorticity OpenMP benchmark.
- `../src/c/mpi_domain_*`: spatial MPI domain decomposition.
- `../src/c/hybrid_mpi_openmp_*`: spatial MPI plus OpenMP threads.

Use the root Makefile for clean builds and smoke tests.
