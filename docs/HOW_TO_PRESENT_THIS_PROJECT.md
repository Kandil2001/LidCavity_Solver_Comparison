# How to present this project

## One-sentence description

A multi-language CFD/HPC benchmark for the lid-driven cavity that compares C, C++, and Python implementations using OpenMP, spatial MPI domain decomposition, and hybrid parallelism, with reproducible result processing and explicit separation of numerical methods.

## Strong technical points

- One-grid MPI domain decomposition with halo exchange.
- Looped and vectorized kernel variants.
- Repeated strong-scaling measurements with median and efficiency.
- Automated repository, build, smoke-output, and result checks.
- Separate pressure-correction validation evidence and streamfunction–vorticity performance evidence.
- Honest treatment of failed builds and incomplete archives.

## Do not claim yet

- a final fastest-language result;
- convergence-controlled time-to-solution;
- a validated CUDA speedup;
- a completed C/C++/Python MPI comparison.
