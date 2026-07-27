# Current Benchmark Results

> **Project status:** Work in progress. This document records the current CPU benchmark dataset and interpretation. It is not a frozen final release.

## Benchmark scope

The benchmark compares the same two-dimensional incompressible lid-driven cavity problem across multiple implementations and programming models.

| Parameter | Values |
|---|---|
| Grid size | `N = 32, 64, 128` |
| Reynolds number | `Re = 100, 400, 1000` |
| Convection schemes | `upwind`, `central` |
| Pressure solvers | `RBGS`, `RBSOR` |
| OpenMP setting | 4 threads |
| MPI setting | case-level parameter-study distribution |

The current dataset was generated on the Stromboli university cluster.

The cleaned result export is stored in:

```text
comparison/results/final_clean/
```

The folder name is retained from the current workflow and does not mean that the full project or benchmark protocol is final.

Selected figures are stored in:

```text
comparison/figures/report_pngs/
comparison/figures/final_clean/
comparison/figures/physics_final/
```

## Execution-status summary

| Solver group | Executed cases | Status |
|---|---:|---|
| `c_serial` | 36 / 36 | execution-complete |
| `cpp_serial` | 36 / 36 | execution-complete |
| `c_openmp_t4` | 36 / 36 | execution-complete |
| `cpp_openmp_t4` | 36 / 36 | execution-complete |
| `python_vectorized` | 36 / 36 | execution-complete |
| `octave_vectorized` | 36 / 36 | execution-complete |
| `c_mpi` | 36 / 36 | execution-complete |
| `cpp_mpi` | 36 / 36 | execution-complete |
| `python_looped` | 20 / 36 | incomplete |
| `octave_looped` | 34 / 36 | incomplete |
| `python_mpi` | 36 / 72 | incomplete |

An execution-complete case reached the end of its configured run. This does not automatically mean that the case met a residual-convergence criterion.

Incomplete groups remain in the tables for transparency but are excluded from the current complete-group ranking.

## Interim runtime summary

Median runtime over the collected case rows:

| Rank | Solver group | Rows | Median runtime [s] |
|---:|---|---:|---:|
| 1 | `c_openmp_t4` | 36 | 236.76 |
| 2 | `cpp_openmp_t4` | 36 | 284.40 |
| 3 | `c_serial` | 36 | 486.39 |
| 4 | `c_mpi` | 36 | 487.40 |
| 5 | `cpp_mpi` | 36 | 630.38 |
| 6 | `cpp_serial` | 36 | 631.80 |
| 7 | `python_mpi` | 36 | 1581.02 |
| 8 | `python_vectorized` | 36 | 1941.31 |
| 9 | `octave_vectorized` | 36 | 2714.37 |
| 10 | `python_looped` | 20 | 4820.14 |
| 11 | `octave_looped` | 34 | 6611.03 |

The current ranking among execution-complete groups is:

1. `c_openmp_t4`
2. `cpp_openmp_t4`
3. `c_serial`
4. `c_mpi`
5. `cpp_mpi`
6. `cpp_serial`
7. `python_vectorized`
8. `octave_vectorized`

These values are specific to the collected hardware, software, parameters, and termination behavior. They are interim execution-time measurements, not a final time-to-convergence ranking.

## Convergence and validation status

The cleaned tables include `AvgPoissonRelResidual` and quality labels.

For the main execution-complete groups, the median `AvgPoissonRelResidual` is approximately:

```text
9.30e-05
```

Quality counts are stored in:

```text
comparison/results/final_clean/quality_counts_by_solver.csv
```

For the complete C, C++, and vectorized Python groups, the current quality split is mostly:

```text
14 cases: needs_improvement
22 cases: validated_but_not_converged
```

This means:

- some cases show useful agreement with the selected Ghia profile thresholds
- some cases reach the maximum iteration limit before meeting the configured convergence criteria
- profile agreement and residual convergence must be reported separately
- the benchmark is useful for implementation and runtime comparison, but the final scientific interpretation is still being refined

## Representative physics outputs

Representative C++ OpenMP outputs are stored in:

```text
comparison/results/physics_fields/
comparison/figures/physics_final/
```

They include:

- velocity-magnitude contours
- pressure contours
- vorticity contours
- streamlines
- velocity-vector fields
- residual histories
- Ghia centerline plots for `u(y)` and `v(x)`

The representative high-resolution case uses:

```text
N = 128
Re = 1000
Scheme = central
Pressure solver = RBSOR
Implementation = C++ OpenMP
```

## Current interpretation

The collected data shows that the compiled implementations are faster than the interpreted workflows for the tested setup. The current lowest median runtime belongs to `c_openmp_t4`, followed by `cpp_openmp_t4`.

C++ OpenMP remains the main practical direction for further solver development because it combines strong performance with clearer structure and maintainability than plain C.

Python remains useful for prototyping, automation, and post-processing.

The MPI implementations distribute independent benchmark cases across ranks. They accelerate parameter sweeps but are not domain-decomposition CFD solvers.

These observations remain provisional until the project includes repeated timings, complete hardware and compiler metadata, and a finalized convergence-aware comparison protocol.

## Accurate project wording

> Work-in-progress multi-language CFD/HPC benchmark for the 2D lid-driven cavity problem, comparing MATLAB/Octave, Python, C, C++, OpenMP, MPI, and a CUDA prototype with runtime tables, residual summaries, Ghia centerline comparisons, and representative flow-field visualizations.

## Files to inspect first

| File or folder | Purpose |
|---|---|
| `comparison/results/final_clean/runtime_summary_fixed.csv` | current runtime table |
| `comparison/results/final_clean/completeness_summary_fixed.csv` | execution-complete and incomplete groups |
| `comparison/results/final_clean/residual_summary_by_solver.csv` | residual summary |
| `comparison/results/final_clean/quality_counts_by_solver.csv` | quality-category summary |
| `comparison/figures/report_pngs/` | runtime, residual, and completeness figures |
| `comparison/figures/physics_final/` | streamlines, contours, vectors, and validation plots |

## Work remaining before a versioned final benchmark

- separate execution, convergence, and validation flags consistently
- add repeated timing measurements and variability statistics
- store compiler, hardware, thread, rank, and commit metadata
- improve high-Reynolds-number convergence behavior
- define the final fair-comparison protocol
- verify numerical equivalence of the CUDA prototype
- publish a versioned release
