# Project overview

This repository studies the two-dimensional incompressible lid-driven cavity across multiple languages, numerical formulations, and parallel programming models.

The project began as a cross-language pressure-correction benchmark and later gained a separate streamfunction–vorticity domain-scaling study. Both tracks are useful, but they must be interpreted independently because they do not currently share one numerical method or stopping protocol.

See [`BENCHMARK_TRACKS.md`](BENCHMARK_TRACKS.md) for the canonical boundary between the two datasets.

## Physical problem

The benchmark uses a square cavity with:

- a moving top lid;
- stationary no-slip side and bottom walls;
- incompressible flow;
- Reynolds-number-controlled test cases;
- comparison against classical Ghia centerline data where field outputs are available.

## Track A — pressure-correction language comparison

The original top-level implementations use an explicit pseudo-time pressure-correction / projection-style workflow:

1. apply velocity boundary conditions;
2. predict the velocity field;
3. solve a pressure-correction Poisson equation;
4. correct velocity and pressure;
5. calculate update, continuity, pressure-solver, and validation metrics;
6. export structured CSV data and figures.

Main locations:

```text
matlab/
python/
c/
cpp/
cuda/
comparison/
```

The original MPI folders distribute independent parameter-study cases across ranks. They are case-level throughput implementations, not spatial domain decomposition.

The current pressure-correction results are pilot data. Several implementations completed the configured matrix, but many cases reached their iteration limit before meeting the current convergence criteria.

## Track B — streamfunction–vorticity scaling study

The organized domain-solver source snapshot under `src/` uses a streamfunction–vorticity formulation and contains:

- OpenMP-only domain solvers;
- MPI domain-decomposition solvers;
- hybrid MPI/threaded solvers;
- looped and vectorization-oriented kernels;
- repeated fixed-step timing studies.

Main locations:

```text
src/
hpc/stromboli/
data/cases/
results/final/
```

These runs provide a substantial execution and scaling archive. A successful row means the process completed; it does not automatically prove convergence or external validation.

## Validation and verification

Current validation evidence includes Ghia centerline comparisons for selected pressure-correction and CUDA outputs. Convergence, validation, and process completion must be reported as separate concepts.

The project still needs formal operator verification, systematic grid trends, common convergence-controlled timing, and cross-language field-equivalence tests before a final software paper benchmark is claimed.

## Current practical interpretation

The repository already demonstrates:

- implementation of the cavity problem in several languages;
- serial, OpenMP, MPI, hybrid, and CUDA programming experience;
- repeated performance-data collection on HPC systems;
- structured post-processing, audits, and result reporting;
- the importance of distinguishing fast execution from a converged and validated numerical solution.

It does not yet support one final fastest-language or CPU-versus-GPU claim.

## Intended publication direction

The first paper should focus on a frozen pressure-correction algorithm across Python, C, C++, and optional Rust. OpenFOAM should be treated as an external engineering reference. The streamfunction–vorticity scaling archive should remain a separate study until its convergence and validation protocol are formalized.
