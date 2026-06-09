# Comparison Scripts

**Role in the project:** compare finished solver outputs.

This folder does not solve the CFD problem. It reads the CSV files written by the solver folders and creates side-by-side comparison tables and reports.

## Contents

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
