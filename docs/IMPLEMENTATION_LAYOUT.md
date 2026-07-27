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

MATLAB follows the same idea as the compiled and Python implementations, but keeps its application scripts under `src/app/`:

```text
matlab/README.md
matlab/Makefile
matlab/main.m                 compatibility entry point
matlab/run_quick.m            compatibility entry point
matlab/run_medium.m           compatibility entry point
matlab/run_smoke.m            compatibility entry point
matlab/src/app/               entry scripts and configuration
matlab/src/core/              numerical operations and SIMPLE loop
matlab/src/studies/           single-case and parametric-study drivers
matlab/src/validation/        Ghia benchmark data and validation helpers
matlab/postprocess/           MATLAB plotting functions
matlab/results/               generated output folders
```

The maintained MATLAB source code is under `src/`. The root-level MATLAB files are kept only so that someone opening the `matlab/` folder directly can run simple commands such as `run_quick`.

## C implementation note

The C solver is one compiled serial baseline. Older names such as `serial_c_looped` and `serial_c_vectorized` are accepted as aliases for compatibility, but they are not two separate C algorithms.

## MPI implementation note

The MPI folders distribute independent benchmark cases across ranks. This is useful for parameter sweeps, but it is not domain decomposition.
