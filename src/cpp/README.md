# C++ domain benchmark

This directory contains the canonical C++ streamfunction–vorticity implementations:

- OpenMP looped/vectorized;
- spatial MPI looped/vectorized;
- hybrid MPI + OpenMP looped/vectorized.

All distributed variants divide one grid among ranks. Build and smoke them from the repository root with `make rebuild-domain` and `make smoke-domain`.
