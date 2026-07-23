# Paper numerical specification

This document defines the first publishable benchmark target. It is intentionally narrower than the full repository so that every reported comparison uses one clear numerical method and one fair stopping protocol.

## Paper question

How consistently and efficiently can the same simple two-dimensional incompressible lid-driven-cavity algorithm be implemented in Python, C, C++, and, when available, Rust?

OpenFOAM is included only as an external engineering reference. The existing MATLAB and Octave implementations remain available in the repository but are not part of the main Stromboli benchmark.

## Fixed physical problem

- Square cavity with side length `L = 1`
- Top-lid velocity `U = 1`
- No-slip stationary side and bottom walls
- Constant density `rho = 1`
- Double precision
- Reynolds numbers `100`, `400`, and `1000`

## Fixed numerical method

The in-house implementations use an explicit pseudo-time pressure-correction method on a uniform Cartesian grid:

1. Apply velocity boundary conditions.
2. Compute a stable pseudo-time step.
3. Predict the velocity field.
4. Compute predicted-velocity divergence.
5. Solve the pressure-correction Poisson equation using red-black SOR.
6. Correct velocity and update pressure.
7. Reapply boundary conditions.
8. Compute velocity-update, divergence, and pressure-solver metrics.
9. Repeat until every required convergence criterion is satisfied.

The method must be described consistently as an explicit pressure-correction or projection-style method. It must not be presented as a new algorithm or as a full finite-volume SIMPLE implementation.

## Main case matrix

The first paper matrix uses:

- Grid sizes: `33`, `65`, `129`, `257`
- Reynolds numbers: `100`, `400`, `1000`
- Convection: central difference
- Diffusion: central difference
- Pressure solver: red-black SOR

This gives 12 primary cases per serial implementation. Odd grid sizes place the geometric centerlines exactly on grid lines.

Upwind and RBGS cases remain useful for development and sensitivity analysis, but they are not part of the main cross-language runtime ranking.

## Initial convergence targets

The draft targets are:

- Maximum velocity update: `1e-8`
- Maximum discrete divergence: `1e-6`
- Pressure Poisson relative residual: `1e-8`
- Pressure solve must converge during the final outer iteration

These values are provisional. A tolerance-sensitivity study must confirm that tightening them further does not materially change the centerline velocities or vortex location.

Reaching the maximum iteration count is never convergence.

## Required status fields

Every result row must contain separate fields for:

- `ExecutionStatus`
- `OuterConverged`
- `PressureConverged`
- `ValidationStatus`

A completed process may therefore still be marked as numerically unconverged.

The current `Ru` and `Rv` quantities should be renamed to `VelocityUpdateU` and `VelocityUpdateV`, because they measure changes between consecutive fields rather than residuals of the discretized momentum equations.

## Validation and verification

### Cavity validation

For each converged case, report:

- Exact `u(y)` profile at `x = 0.5`
- Exact `v(x)` profile at `y = 0.5`
- L1, L2, and Linf errors against Ghia et al.
- Primary-vortex center and velocity or streamfunction measure
- Grid trend across all available resolutions

Validation thresholds must not be used as substitutes for convergence.

### Code verification

Before final timing runs, add tests for:

- First derivatives of analytical polynomial fields
- Laplacian of an analytical field
- Divergence of an analytical divergence-free field
- Vorticity of an analytical field
- Pressure Poisson solution with a known analytical answer
- Boundary-condition application

The tests should show the expected discretization order under systematic grid refinement.

## Cross-language equivalence

The C++ serial implementation is the initial numerical reference. Once it converges reliably, the same case must be reproduced in C, Python, and optional Rust.

For matched converged fields, report differences in:

- `u`, `v`, and speed L1/L2/Linf norms
- Mean-centered pressure norms
- Maximum divergence
- Centerline profiles
- Outer-iteration count
- Total pressure iterations

Serial and shared-memory versions must agree within documented floating-point tolerances before they are timed.

## Language and software scope

### Core serial implementations

- Python/NumPy
- C
- C++

### Conditional serial implementation

- Rust, only after `rustc` and `cargo` availability is confirmed on Stromboli or a reproducible user-space toolchain is established

### Shared-memory comparison

- C/OpenMP
- C++/OpenMP
- Rust/Rayon when Rust is available

### MPI

The current MPI drivers distribute independent cases. They must be evaluated as parameter-sweep throughput using total study wall time and cases per hour. They are not domain-decomposed CFD solvers.

### OpenFOAM

OpenFOAM is an external reference for centerline accuracy, vortex structure, and end-to-end runtime. It must be plotted separately from the identical-algorithm language ranking.

### Excluded from the first paper

- MATLAB and Octave, because they are unavailable on the target Stromboli environment
- CUDA, until an algorithmically equivalent pressure solve is available

## Timing protocol

Final timing runs must:

- Use only converged cases
- Run on the same node type
- Record hostname, CPU, compiler/interpreter version, commit SHA, thread count, and rank count
- Disable field output inside the timed solver section
- Use one warm-up and at least five measured repetitions
- Preserve every individual timing result
- Report median and interquartile range
- Report solver time separately from output and total process time

## Existing long-running jobs

Jobs started before this specification should be allowed to finish and archived as `pilot_v0`. They are useful for diagnosing convergence and estimating runtime, but they must not be included in the final paper ranking unless they are rerun under the frozen specification.

## First acceptance milestone

The first milestone is one C++ serial case:

```text
N = 65
Re = 100
Convection = central
Pressure solver = RBSOR
```

It must:

- satisfy all convergence criteria;
- produce a stable pressure residual history;
- match the Ghia centerlines within a documented error;
- export complete metadata;
- reproduce consistently in repeated runs.
