# Results guide

## Start here

- `results/selected/README.md`: the compact reviewed result set used by the root README.
- `results/selected/highlights.csv`: one best vectorized point per retained implementation.
- `results/selected/scaling_case_n128_re400_central_rbsor.csv`: every scaling point for the selected case.
- `results/selected/execution_completeness.csv`: archive-level success and failure totals.

Regenerate these files without running CFD:

```bash
python3 scripts/generate_selected_results.py
```

## Full domain archive

- `results/final/cpu_case_summaries/`: per-case repeated scaling summaries.
- `results/final/comparisons/`: completeness and combined archive tables.
- `results/final/figures/`: detailed archived figures.
- `results/final/README_FINAL_STATUS.md`: audit of the complete package.

The full archive is retained for traceability, but it is not all suitable for headline comparison.

## Pressure-correction reference evidence

- `comparison/results/physics_fields/`
- `comparison/figures/physics_final/`

These files belong to the earlier numerical method and are not merged with domain timings.

## CUDA

- `results/cuda/cuda_validation_summary.csv`
- `results/cuda/cuda_cpu_exact_full_summary.csv`

The archived CUDA validation does not currently pass, so CUDA is not included in selected performance results.

## Reporting rule

Never collapse language, kernel style, pressure solver, resource count, or repetition into one unlabeled minimum. Use matched configurations and report median plus variability.
