# Python domain benchmark

This directory contains the canonical Python streamfunction–vorticity distributed implementations:

- spatial MPI looped/vectorized;
- hybrid MPI + local threaded kernels, looped/vectorized.

Each rank owns a grid slab and exchanges halos with neighboring ranks. Use `make smoke-domain-mpi` and `make smoke-domain-hybrid` from the repository root.
