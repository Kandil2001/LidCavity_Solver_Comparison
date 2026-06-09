# Implementation layout

The repository is organised so that every implementation feels like the same project written for a different platform.

## Standard implementation structure

Most implementation folders follow this pattern:

```text
README.md        What this implementation does and how to run it
Makefile         Common run commands
src/             Solver source code
postprocess/     Plotting or post-processing scripts
results/         Generated outputs, kept mostly empty in Git
```

## Standard result structure

```text
results/data/      CSV summaries, field data, residual histories
results/figures/   generated plots
results/scaling/   OpenMP, MPI, or CUDA scaling tables
results/logs/      optional logs from long runs
```

## MATLAB note

The MATLAB implementation also uses the same idea, but its solver functions are grouped inside `matlab/src/`:

```text
matlab/src/core/          numerical operations and SIMPLE loop
matlab/src/studies/       parametric-study drivers
matlab/src/validation/    Ghia benchmark data and validation helpers
matlab/src/postprocess/   MATLAB plotting functions
```

This keeps the MATLAB folder consistent with the other platforms while still keeping the MATLAB workflow readable.
