# Comparison scripts

This folder is used after the solver folders have produced their CSV outputs.

The solvers stay independent while running. The comparison scripts then read the finished summaries and field files and write side-by-side tables and plots.

## From the repository root

```bash
make compare-serial MODE=quick
make report-serial MODE=quick
```

## Direct commands

```bash
python3 compare_outputs.py \
  --reference-data ../matlab/results/data \
  --reference-summary study_summary_quick_matlab.csv \
  --cpp-data ../cpp/serial/results/data \
  --cpp-summary study_summary_quick.csv \
  --c-data ../c/serial/results/data \
  --c-summary study_summary_quick.csv \
  --python-data ../python/serial/results/data \
  --python-summary study_summary_quick.csv \
  --out results
```

The final files are written to `comparison/results/`.

## If MATLAB is not available

You can still compare the CPU solvers by using C++ as the reference:

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
