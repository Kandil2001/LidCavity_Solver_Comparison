# Project overview

This project studies the two-dimensional incompressible lid-driven cavity as a CFD implementation and HPC benchmark.

## Main research questions

1. How similar are C and C++ implementations of the same domain solver?
2. When does OpenMP reduce runtime, and when does synchronization overhead dominate?
3. How does one spatially decomposed simulation scale across MPI ranks?
4. Does a hybrid MPI + threading layout outperform pure MPI for the same total core count?
5. How do looped and vectorized kernels change performance?

## Canonical numerical track

The domain benchmark uses streamfunction–vorticity solvers under `src/`. Configurations preserve:

- language;
- parallel model;
- looped or vectorized kernel;
- grid size and Reynolds number;
- convection and Poisson method;
- step counts;
- MPI ranks and thread counts;
- repeated runtime statistics.

## Earlier reference work

The top-level serial/OpenMP implementations use a pressure-correction formulation and retain useful validation evidence. They are kept as a separate reference track rather than being forced into the same runtime ranking.

## Evidence standard

Execution completion, numerical convergence, validation, and runtime repeatability are reported separately. The current domain archive is fixed-step performance evidence, not a frozen convergence-controlled paper dataset.
