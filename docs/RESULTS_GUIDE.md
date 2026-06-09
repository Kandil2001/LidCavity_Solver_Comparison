# Results guide

Each implementation writes its own result files under its own folder. This keeps the solvers independent and avoids mixing unfinished runs.

Typical output folders:

```text
results/data/      CSV summaries, fields, and residual histories
results/figures/   plots from the post-processing scripts
results/scaling/   scaling tables for parallel versions
```

## Main summary file

A run usually creates a file like:

```text
results/data/study_summary_quick.csv
```

For MATLAB the mode name includes `_matlab`, for example:

```text
results/data/study_summary_quick_matlab.csv
```

## Field files

Field files are named by case setup. A typical file name contains:

```text
N, Re, scheme, pressure solver, implementation
```

This is useful because the comparison scripts match cases by setup, not by the order in which they were run.

## Comparison outputs

After running serial implementations, use:

```bash
make compare-serial MODE=quick
make report-serial MODE=quick
```

The output goes to:

```text
comparison/results/
```

The most useful files are:

- `comparison_summary.csv`
- `benchmark_report.md`
- `runtime_pivot_by_case.csv`
- `aggregate_by_implementation.csv`
- runtime plots as `.png`

## What to upload to GitHub

Good files to keep:

- source code,
- Makefiles,
- README files,
- selected final reports,
- selected final plots.

Usually do not commit:

- raw full field CSV files from every run,
- temporary logs,
- local build folders,
- Python cache folders.
