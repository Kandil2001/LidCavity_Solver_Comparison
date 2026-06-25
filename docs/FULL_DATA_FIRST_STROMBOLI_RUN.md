# Full data-first Stromboli run, no CUDA

This workflow is designed for Stromboli CPU nodes. It uses Slurm jobs so that
nothing heavy runs on the login/front-end node.

## Why this workflow

The full study already includes the grid sweep:

- `N = 32, 64, 128`
- `Re = 100, 400, 1000`
- schemes: `upwind`, `central`
- pressure solvers: `RBGS`, `RBSOR`

So grid convergence should be calculated from the full-study results rather
than by rerunning a separate 3-case convergence demo.

## What is generated

The workflow generates CSV and Markdown comparison files only:

- solver summary tables
- residual-history summaries
- runtime and validation comparisons
- grid-convergence orders from existing full-study grids
- plot-candidate report

It does **not** generate final PNG/PDF plot images. Those should be created only
after the useful cases are selected.

## Submit the full study

From the repository root on the Stromboli login node:

```bash
cd ~/LidCavity_Solver_Comparison
chmod +x scripts/*.sh
bash scripts/submit_stromboli_full_data_first_no_cuda.sh
```

This command only submits jobs. The solvers run inside Slurm allocations.

## Watch progress

```bash
squeue -u $USER
tail -f logs/lid_*_data_*.out logs/lid_full_data_post_*.out
```

Stop watching with `CTRL+C`. This does not cancel the jobs.

## Results to inspect first

After the postprocessing job finishes, check:

```bash
ls comparison/results/data_first
cat comparison/results/data_first/full_study_data_report.md
cat comparison/results/data_first/plot_candidates_no_images_yet.md
```

Important CSV files:

```text
comparison/results/data_first/all_case_summary.csv
comparison/results/data_first/grid_convergence_all.csv
comparison/results/data_first/residual_history_summary.csv
comparison/results/data_first/casewise_relative_to_cpp_serial.csv
comparison/results/data_first/top3_fastest_per_case.csv
comparison/results/data_first/top3_lowest_error_per_case.csv
comparison/results/data_first/scheme_pressure_summary.csv
```

## CPU layout note

The shown Stromboli CPU has 16 physical cores and 32 logical CPUs:

- 2 sockets
- 8 physical cores per socket
- 2 hardware threads per core

For clean portfolio timing, this workflow uses scaling up to 8 threads/ranks.
That avoids overselling hyperthreading effects and gives a fairer physical-core
benchmark.
