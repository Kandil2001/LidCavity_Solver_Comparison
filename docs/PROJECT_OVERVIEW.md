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

The comparison is not expected to be bit-for-bit identical between languages. The useful checks are residual history, velocity fields, centerline profiles, validation error, and runtime trend.

## Implementation levels

- Reference workflow: MATLAB
- Readable serial workflow: Python / NumPy
- Compiled serial baselines: C and C++
- Shared-memory parallelism: C/OpenMP and C++/OpenMP
- Case-level distributed runs: Python/MPI, C/MPI, C++/MPI
- Automated studies: grid-convergence tables, Ghia centerline plots, OpenMP/MPI scaling plots
- GPU prototype: CUDA

## Current limitations

- The MPI versions are case-level runners, not domain-decomposition solvers.
- The CUDA version is a GPU prototype and should be compared carefully with the CPU solvers.
- Python serial and Python MPI can use the Python NumPy/vectorized-style and loop-style implementation labels.
- C/C++ OpenMP and C/C++ MPI are single baseline implementations, not separate looped/vectorized algorithms.
- The C solver is one compiled baseline; older looped/vectorized labels are aliases only.
- Full benchmark conclusions should be added only after running the complete study on the target machine.
