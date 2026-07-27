# Benchmark tracks and evidence boundaries

This repository contains two related lid-driven-cavity benchmark tracks. They solve the same physical problem, but they do not currently use the same numerical formulation or stopping protocol. Results from the two tracks must therefore be reported separately.

## Track A — cross-language pressure-correction benchmark

### Purpose

Compare a common explicit pseudo-time pressure-correction / projection-style workflow across programming languages and shared-memory implementations.

### Main locations

```text
matlab/
python/serial/
python/mpi/
c/serial/
c/openmp/
c/mpi/
cpp/serial/
cpp/openmp/
cpp/mpi/
cuda/
comparison/
```

### Numerical scope

- velocity prediction followed by a pressure-correction Poisson solve
- velocity and pressure correction
- RBGS and RBSOR pressure solvers on the CPU
- upwind and central convection options
- Ghia centerline comparisons

The original `python/mpi`, `c/mpi`, and `cpp/mpi` folders distribute independent cases over MPI ranks. They are parameter-sweep runners, not spatial domain-decomposition solvers.

### Current evidence

The cleaned pilot results are under:

```text
comparison/results/final_clean/
comparison/results/physics_fields/
comparison/figures/report_pngs/
comparison/figures/physics_final/
```

These files contain useful execution, residual, profile, and runtime evidence. Many cases reached their configured iteration limit, so the dataset is a pilot execution-time study rather than a final time-to-convergence benchmark.

## Track B — streamfunction–vorticity domain-scaling benchmark

### Purpose

Study OpenMP, MPI domain decomposition, and hybrid MPI/thread scaling with repeated fixed-step runs.

### Main locations

```text
src/c/
src/cpp/
src/python/
hpc/stromboli/
data/cases/
results/final/
results/audits/
```

### Numerical scope

- streamfunction–vorticity formulation
- fixed configured outer-step counts
- RBGS and RBSOR Poisson options
- looped and vectorization-oriented kernels
- OpenMP, MPI domain decomposition, and hybrid parallel models

The `src/` track is numerically different from Track A. Its timing results must not be merged with the pressure-correction results as if they were implementations of one identical algorithm.

### Current evidence

The archived repeated results are under:

```text
results/final/cpu_case_summaries/
results/final/comparisons/
results/final/figures/
results/cuda/
```

In these files, `status=success` means that the process completed and a summary row was produced. It does not by itself establish numerical convergence or Ghia validation.

## CUDA evidence

The current A100 RBGS/RBSOR archive is projection-based and is therefore not numerically identical to the streamfunction–vorticity CPU domain track. The current validation table reports no passing CUDA cases under the configured Ghia thresholds.

CUDA timing tables may be retained as experimental implementation measurements, but they must not be presented as validated CPU-versus-GPU speedups.

## Reporting rules

When adding tables, figures, or README claims:

1. State the numerical track.
2. Keep pressure-correction and streamfunction–vorticity results separate.
3. Distinguish process completion from numerical convergence.
4. Distinguish convergence from external validation.
5. Preserve language, implementation, kernel, pressure solver, core count, rank count, thread count, and repetition in aggregated data.
6. Use repeated-run medians and variability for performance conclusions; do not use only the minimum observed runtime.
7. Label archived fixed-step results as fixed-step execution measurements.

## Intended paper direction

The first software paper should use the narrower pressure-correction track with one frozen algorithm and convergence protocol across Python, C, C++, and optional Rust. OpenFOAM should be an external reference. The streamfunction–vorticity scaling archive can remain a separate study until its validation and stopping protocol are formalized.
