# Comparison Scripts

**Role in the project:** compare finished solver outputs.

This folder does not solve the CFD problem itself. It reads the CSV files written by the solver folders and creates side-by-side comparison tables and reports.

The solvers stay independent while running. The comparison step happens only after the selected implementations have produced their results.

## What this folder contains

| File | Purpose |
|---|---|
| `compare_outputs.py` | Match cases and compare result summaries |
| `benchmark_report.py` | Create benchmark tables and report files |
| `postprocess/plot_parallel_scaling.py` | Plot OpenMP/MPI/CUDA scaling results |
| `requirements.txt` | Python dependencies |
| `results/` | Generated comparison outputs |

## Run from the repository root

After running the serial implementations:

```bash
make compare-serial MODE=quick
make report-serial MODE=quick
```

The output is written to:

```text
comparison/results/
```

## Direct comparison command

```bash
python3 compare_outputs.py \
  --reference-data ../matlab/results/data \
  --reference-summary study_summary_quick_matlab.csv \
  --reference-label MATLAB \
  --cpp-data ../cpp/serial/results/data \
  --cpp-summary study_summary_quick.csv \
  --c-data ../c/serial/results/data \
  --c-summary study_summary_quick.csv \
  --python-data ../python/serial/results/data \
  --python-summary study_summary_quick.csv \
  --out results
```

## If MATLAB is not available

You can still compare CPU solvers by using C++ as the reference:

```bash
python3 comparison/compare_outputs.py \
  --reference-data cpp/serial/results/data \
  --reference-summary study_summary_smoke.csv \
  --reference-label C++ \
  --c-data c/serial/results/data \
  --c-summary study_summary_smoke.csv \
  --python-data python/serial/results/data \
  --python-summary study_summary_smoke.csv \
  --out comparison/results
```

## Matching logic

Cases are matched by setup:

```text
mesh size, Reynolds number, convection scheme, pressure solver
```

This is safer than matching by case number because different solvers may write files in a different order.

## Notes

- Run the solvers first, then run comparison.
- Keep only selected final reports and plots in GitHub.
- Avoid committing large raw field CSV files from every benchmark run.
