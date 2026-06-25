# Final Benchmark Results

This document summarizes the final CPU benchmark run for the lid-driven cavity solver comparison project.

## Benchmark scope

The benchmark compares the same 2D incompressible lid-driven cavity problem across multiple implementations and programming models.

| Parameter | Values |
|---|---|
| Grid size | `N = 32, 64, 128` |
| Reynolds number | `Re = 100, 400, 1000` |
| Convection schemes | `upwind`, `central` |
| Pressure solvers | `RBGS`, `RBSOR` |
| OpenMP setting | 4 threads |
| MPI setting | case-level parameter-study distribution |

The benchmark was run on the Stromboli university cluster. The final clean results are stored in:

```text
comparison/results/final_clean/
```

Selected final figures are stored in:

```text
comparison/figures/report_pngs/
comparison/figures/final_clean/
comparison/figures/physics_final/
```

## Completion summary

| Solver group | Completed cases | Status |
|---|---:|---|
| `c_serial` | 36 / 36 | complete |
| `cpp_serial` | 36 / 36 | complete |
| `c_openmp_t4` | 36 / 36 | complete |
| `cpp_openmp_t4` | 36 / 36 | complete |
| `python_vectorized` | 36 / 36 | complete |
| `octave_vectorized` | 36 / 36 | complete |
| `c_mpi` | 36 / 36 | complete |
| `cpp_mpi` | 36 / 36 | complete |
| `python_looped` | 20 / 36 | incomplete |
| `octave_looped` | 34 / 36 | incomplete |
| `python_mpi` | 36 / 72 | incomplete |

The incomplete solvers are kept in the result tables for transparency. They are not used for the main complete-solver ranking.

## Runtime summary

Median runtime over collected cases:

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

For a fair complete-solver ranking, use only the completed groups:

1. `c_openmp_t4`
2. `cpp_openmp_t4`
3. `c_serial`
4. `c_mpi`
5. `cpp_mpi`
6. `cpp_serial`
7. `python_vectorized`
8. `octave_vectorized`

## Convergence and validation summary

The clean result tables include `AvgPoissonRelResidual` and quality labels. Most complete solvers show essentially the same residual pattern because they solve the same benchmark cases.

For the main complete solvers, the median `AvgPoissonRelResidual` is approximately:

```text
9.30e-05
```

The quality labels are stored in:

```text
comparison/results/final_clean/quality_counts_by_solver.csv
```

For the complete C/C++/Python-vectorized groups, the quality split is mostly:

```text
14 cases: needs_improvement
22 cases: validated_but_not_converged
```

This should be interpreted honestly: the benchmark is useful for comparing implementation behaviour and runtime, but some cases reach the maximum iteration limit before full convergence. The result plots and tables therefore emphasize both performance and numerical quality.

## Representative physics outputs

Representative C++ OpenMP field outputs were generated for selected cases and stored in:

```text
comparison/results/physics_fields/
comparison/figures/physics_final/
```

These figures include:

- velocity magnitude contours
- pressure contours
- vorticity contours
- streamlines
- velocity vector fields
- residual histories
- Ghia centerline validation plots for `u(y)` and `v(x)`

The representative high-resolution example uses:

```text
N = 128
Re = 1000
Scheme = central
Pressure solver = RBSOR
Implementation = C++ OpenMP
```

## Main interpretation

For this lid-driven cavity benchmark, the compiled implementations were much faster than the interpreted workflows. The fastest complete implementation was `c_openmp_t4`, followed by `cpp_openmp_t4`.

C OpenMP gave the best raw runtime. C++ OpenMP is the best practical direction for further solver development because it combines strong performance with cleaner structure and better maintainability than plain C.

Python remains valuable for prototyping, automation, and post-processing. Pure Python loops and looped Octave are not suitable for heavy CFD parameter sweeps without further acceleration.

The MPI implementations in this repository are case-level parameter-study parallel implementations. They distribute independent benchmark cases across ranks. They are useful for running a sweep faster, but they are not domain-decomposition CFD solvers.

## Recommended project wording

A concise professional description for this repository:

> Multi-language CFD/HPC benchmark for the 2D lid-driven cavity problem, comparing MATLAB/Octave, Python, C, C++, OpenMP, MPI, and CUDA-style workflows with runtime tables, residual summaries, Ghia validation plots, and representative flow-field visualizations.

## Files to cite or show first

| File/folder | Purpose |
|---|---|
| `comparison/results/final_clean/runtime_summary_fixed.csv` | final runtime ranking |
| `comparison/results/final_clean/completeness_summary_fixed.csv` | completed vs incomplete solver groups |
| `comparison/results/final_clean/residual_summary_by_solver.csv` | residual/convergence summary |
| `comparison/results/final_clean/quality_counts_by_solver.csv` | quality-category summary |
| `comparison/figures/report_pngs/` | report-level runtime/residual/completeness plots |
| `comparison/figures/physics_final/` | streamlines, contours, vectors, and validation plots |
