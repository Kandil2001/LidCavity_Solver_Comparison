# Final Plots and Comparisons

This folder contains final comparison CSV tables and SVG figures.

## Main Tables

- `comparisons/cpu_completeness_status.csv`
- `comparisons/cpu_success_failed_overview.csv`
- `comparisons/cpu_successful_runtime_rows.csv`
- `comparisons/cpu_best_runtime_by_case.csv`
- `comparisons/cuda_full_rbgs_rbsor_rows.csv`
- `comparisons/cuda_runtime_by_pressure_solver.csv`
- `comparisons/cuda_best_runtime_by_case.csv`
- `comparisons/combined_best_runtime_by_case_backend.csv`

## Main Figures

- `figures/cpu_success_failed_overview.svg`
- `figures/cpu_best_runtime_by_case.svg`
- `figures/cuda_median_runtime_by_pressure_solver.svg`
- `figures/combined_best_runtime_by_case_backend.svg`

## Notes

Runtime comparisons use successful rows only.
MPI and hybrid case 13 were salvaged from successful rows.
Failed/time-limited rows are reported separately in the completeness tables.
CUDA validation is reported separately from runtime.
