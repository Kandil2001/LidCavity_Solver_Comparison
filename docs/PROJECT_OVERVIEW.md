# Project overview

This project compares several implementations of the same CFD benchmark: the two-dimensional lid-driven cavity.

The purpose is not to build the biggest solver. The purpose is to keep the physical problem fixed and then study what changes when the same idea is written in MATLAB, Python, C, C++, OpenMP, MPI, and CUDA.

## Benchmark problem

The case is a square cavity with:

- a moving top lid,
- no-slip side and bottom walls,
- incompressible flow,
- Reynolds numbers such as 100, 400, and 1000,
- centerline velocity validation against the Ghia et al. data.

## Numerical idea

The implementations follow a SIMPLE-style pressure-correction workflow:

1. apply boundary conditions,
2. predict velocity,
3. solve pressure correction,
4. correct velocity and pressure,
5. monitor residuals and validation metrics,
6. export CSV files for comparison.

## What is fair to compare

The most useful comparison is not only runtime. A useful comparison checks:

- whether the same case setup was used,
- whether the residuals behave similarly,
- whether the centerline profiles are close,
- whether the Ghia validation errors are reasonable,
- how much speed is gained by changing language or parallel strategy.

## What is not claimed

The MPI code is currently case-parallel, not domain-decomposed. The CUDA code is kept separate because it needs a GPU machine. The project is a portfolio and learning benchmark, not a replacement for OpenFOAM, STAR-CCM+, or ANSYS Fluent.
