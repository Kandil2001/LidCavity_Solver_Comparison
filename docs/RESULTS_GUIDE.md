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

## Git policy

Generated result files are ignored by Git by default. Keep only selected final plots or tables that are worth showing in the main README.
