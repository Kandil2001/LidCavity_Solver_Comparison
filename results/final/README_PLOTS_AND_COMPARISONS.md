# Archived plots and comparisons

This folder contains retained tables and figures from the streamfunction–vorticity domain-scaling study and the separate CUDA A100 archive.

These files are useful for execution and performance diagnostics. They are not one validated same-algorithm CPU/GPU benchmark.

See:

- [`README_FINAL_STATUS.md`](README_FINAL_STATUS.md)
- [`../../docs/BENCHMARK_TRACKS.md`](../../docs/BENCHMARK_TRACKS.md)
- [`../../docs/RESULTS_GUIDE.md`](../../docs/RESULTS_GUIDE.md)

## Main completeness tables

- `comparisons/cpu_completeness_status.csv`
- `comparisons/cpu_success_failed_overview.csv`
- `comparisons/cpu_successful_runtime_rows.csv`

These files preserve successful and failed/time-limited execution counts. In the archived raw rows, success means process completion rather than a universal convergence decision.

## Detailed scaling tables

- `cpu_all_strong_scaling_summaries.csv`
- `cpu_all_best_by_solver.csv`
- `cpu_case_summaries/`

Use detailed fixed-configuration rows whenever possible. Preserve language, solver, kernel, pressure method, core count, rank count, thread count, and repetition.

## Exploratory broad comparisons

- `comparisons/cpu_best_runtime_by_case.csv`
- `comparisons/cuda_best_runtime_by_case.csv`
- `comparisons/combined_best_runtime_by_case_backend.csv`

These tables select broad minimum runtimes and can collapse several configuration dimensions. They are retained for exploration and historical traceability, not as paper-quality rankings.

## Figures

- `figures/cpu_success_failed_overview.svg`
- `figures/cpu_best_runtime_by_case.svg`
- `figures/cuda_median_runtime_by_pressure_solver.svg`
- `figures/combined_best_runtime_by_case_backend.svg`

Interpret the broad backend figures cautiously. The CPU domain archive uses streamfunction–vorticity, while the CUDA archive is projection-based and currently fails the configured Ghia validation thresholds.

## Reporting requirements for regenerated figures

Future regenerated tables and plots should:

1. use median runtime for each fixed configuration;
2. show run count and variability such as IQR or standard deviation;
3. label RBGS and RBSOR separately;
4. keep looped and vectorized kernels separate;
5. keep C, C++, and Python separate;
6. state whether rows are fixed-step or convergence-controlled;
7. report execution, convergence, and validation status independently;
8. avoid connecting different pressure solvers as one scaling curve.
