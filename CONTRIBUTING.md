# Contributing

Thank you for your interest in contributing to this lid-driven cavity CFD benchmark.

This project is primarily a portfolio and learning project, so contributions should keep the repository clear, reproducible, and scientifically honest.

## Good contribution areas

Useful contributions include:

- fixing build or runtime issues
- improving documentation
- improving reproducibility on Linux/HPC systems
- adding small validation or plotting improvements
- improving post-processing scripts
- adding benchmark cases in a controlled way
- improving code clarity without changing numerical behaviour silently

## Before changing solver behaviour

If a change affects numerical results, please document:

- which implementation is affected
- what changed numerically
- whether the change affects runtime
- whether the change affects validation against Ghia data
- whether previous benchmark tables need to be regenerated

## Development workflow

1. Create a feature branch.
2. Make focused changes.
3. Run a smoke test when possible.
4. Keep generated temporary outputs out of Git.
5. Open a pull request with a clear summary.

Example smoke commands:

```bash
make smoke-cpu
```

or for one implementation:

```bash
cd cpp/serial
make smoke
```

## Generated files

Do not commit large raw result folders, temporary work folders, build products, local logs, or packaged archives.

The important final report folders currently kept in Git are:

```text
comparison/results/final_clean/
comparison/results/physics_fields/
comparison/figures/final_clean/
comparison/figures/report_pngs/
comparison/figures/physics_final/
```

## Code style

General expectations:

- use readable names
- avoid unnecessary complexity
- keep implementation-specific changes inside the relevant folder
- document assumptions near the code that uses them
- avoid claiming exact equivalence across languages unless it is actually verified

## Scientific honesty

This repository should be presented as a benchmark and learning project, not as a production-grade CFD solver.

Important scope notes:

- MPI is currently case-level parameter-study parallelism, not domain decomposition.
- CUDA is a prototype and should be compared carefully.
- Some cases reach the maximum iteration limit before full convergence.
- Incomplete solver groups are retained for transparency but should not be used for the fair complete-solver ranking.
