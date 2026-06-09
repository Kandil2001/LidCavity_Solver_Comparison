# Project overview

This repository compares multiple implementations of the same CFD benchmark: the two-dimensional incompressible lid-driven cavity.

The project started from a MATLAB reference workflow and was then extended into Python, C, C++, OpenMP, MPI, and CUDA versions. The aim is to compare implementation style, output consistency, validation behaviour, and runtime trends.

## Numerical idea

The cavity has a moving top lid and no-slip walls. The solver uses a SIMPLE-style pressure-correction workflow:

1. apply velocity and pressure boundary conditions
2. predict the velocity field
3. solve a pressure-correction equation
4. correct pressure and velocity
5. compute residuals and validation values
6. export CSV files for comparison

## Validation

Centerline velocity profiles are compared against the classical Ghia et al. lid-driven cavity benchmark data where applicable.

## Parallelisation levels

- Serial implementations: MATLAB, Python, C, C++
- Shared-memory parallelism: C/OpenMP and C++/OpenMP
- Case-level distributed runs: Python/MPI, C/MPI, C++/MPI
- GPU prototype: CUDA

The MPI versions currently distribute independent benchmark cases. They are not domain-decomposition CFD solvers yet.
