# Results guide

Each implementation writes outputs to its own `results/` folder. This avoids mixing files from different languages and makes comparisons easier.

## Standard result folders

```text
results/data/      CSV summaries, field data, residual histories, validation data
results/figures/   velocity plots, residual plots, validation plots
results/scaling/   OpenMP, MPI, or CUDA scaling tables
results/logs/      optional long-run logs
```

## Comparison workflow

1. Run at least one serial implementation.
2. Run another implementation with the same mode.
3. From the repository root, run:

```bash
make compare-serial MODE=quick
make report-serial MODE=quick
```

The comparison scripts match cases by setup:

```text
mesh size, Reynolds number, convection scheme, pressure solver
```

This is safer than matching only by case number or file order.


## Automated studies

Grid convergence from the repository root:

```bash
make grid-convergence
```

This writes CSV and PNG files to:

```text
comparison/results/grid_convergence/
```

The observed order is based on centerline L2 errors against the Ghia benchmark data. It is useful for comparing grid trends, but it is not the same as a manufactured-solution accuracy proof.

Automatic validation plots:

```bash
make validation-plots
python3 scripts/plot_validation_centerlines.py --Re 100 --N 64
```

Parallel scaling plots:

```bash
make scaling-openmp
make scaling-mpi MODE=quick
```

OpenMP scaling is a fixed-case strong-scaling check. MPI scaling is case-level parameter-sweep scaling, not one-domain domain-decomposition scaling.

## Reading runtime results

Use runtime trends carefully:

- smoke runs check that the code starts; they are not reliable performance measurements
- OpenMP can be slower on very small grids because thread overhead dominates
- MPI speedup here means faster parameter studies, not faster solution of one domain
- CUDA should be tested only on a real NVIDIA GPU with the CUDA toolkit installed

## Git policy

Generated result files are ignored by Git by default. Keep only selected final plots or tables that are worth showing in the main README.
