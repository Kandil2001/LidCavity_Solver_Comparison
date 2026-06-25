# Comparison Scripts

**Role in the project:** compare finished solver outputs and create portfolio-level result plots.

This folder does not solve the CFD problem. It reads the CSV files written by the solver folders and creates side-by-side comparison tables, validation plots, convergence tables, and scaling plots.

## Contents

| File | Purpose |
|---|---|
| `compare_outputs.py` | Match cases and compare result summaries |
| `benchmark_report.py` | Create benchmark tables and report files |
| `postprocess/plot_parallel_scaling.py` | Plot OpenMP/MPI/CUDA scaling results |
| `requirements.txt` | Python dependencies |
| `results/` | Generated comparison outputs |

Root-level helper scripts that write into this folder:

| Script | Purpose |
|---|---|
| `../scripts/run_grid_convergence.py` | Run selected serial solver across progressively finer grids and estimate observed order |
| `../scripts/plot_validation_centerlines.py` | Plot U/V centerline validation against Ghia data |
| `../scripts/run_parallel_scaling.py` | Run OpenMP/MPI scaling checks and generate scaling plots |

## Run from the repository root

After running the serial implementations:

```bash
make compare-serial MODE=quick
make report-serial MODE=quick
```

Grid convergence:

```bash
make grid-convergence
```

Validation centerline plots:

```bash
make validation-plots
```

Parallel scaling:

```bash
make scaling-openmp
make scaling-mpi MODE=quick
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

## Notes on interpretation

- C is reported as one compiled serial baseline. Older C looped/vectorized labels are treated as aliases only.
- Python and MATLAB have clearer loop-style and vectorized/NumPy-style study paths.
- Python MPI distributes both Python implementation labels when they are part of the configured case list.
- C/C++ OpenMP and C/C++ MPI are not separate looped/vectorized algorithms.
- MPI results describe case-level parameter-study parallelism, not domain decomposition.
- Grid-convergence order is calculated against benchmark centerline data, not an exact manufactured solution.

## Notes

- Run the solvers first, then run comparison/plotting scripts.
- Keep only selected final reports and plots in GitHub.
- Avoid committing large raw field CSV files from every benchmark run.
