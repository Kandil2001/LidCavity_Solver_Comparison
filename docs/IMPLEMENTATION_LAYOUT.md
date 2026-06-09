# Implementation layout

The repository is organised so that every implementation feels like the same project written for a different platform.

## Standard implementation structure

Most implementation folders follow this pattern:

```text
README.md        What this implementation does and how to run it
Makefile         Common build/run commands
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

## MATLAB layout

MATLAB follows the same idea as the compiled and Python implementations. The only difference is that MATLAB scripts are grouped inside `src/app/` and solver functions are grouped by role:

```text
matlab/README.md
matlab/Makefile
matlab/src/app/          entry scripts and configuration
matlab/src/core/         numerical operations and SIMPLE loop
matlab/src/studies/      single-case and parametric-study drivers
matlab/src/validation/   Ghia benchmark data and validation helpers
matlab/postprocess/      MATLAB plotting functions
matlab/results/          generated output folders
```

The old duplicate MATLAB folders (`core/`, `post/`, `studies/`, and `validation/` at the MATLAB root) were removed so there is only one source layout.
