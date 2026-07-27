# MATLAB Reference Solver

**Role:** Reference workflow  
**Language/platform:** MATLAB or GNU Octave

This folder contains the MATLAB/Octave reference implementation. It keeps the numerical workflow easy to inspect and is useful for checking the other implementations.

## Run

Auto-detect MATLAB first, then GNU Octave:

```bash
make smoke
make quick
make medium
```

Force GNU Octave, useful on Stromboli or other university machines without MATLAB:

```bash
make smoke ENGINE=octave
make quick ENGINE=octave
make medium ENGINE=octave
```

Force MATLAB:

```bash
make smoke ENGINE=matlab
```

## Single case example

```bash
make single
```

## Folder layout

| Path | Purpose |
|---|---|
| `Makefile` | MATLAB run commands |
| `src/app/` | Entry scripts and configuration |
| `src/core/` | Numerical operators and SIMPLE loop |
| `src/studies/` | Single-case and parametric-study drivers |
| `src/validation/` | Ghia centerline validation data and checks |
| `postprocess/` | MATLAB plotting functions |
| `results/` | Generated CSV, figures, scaling, and logs |

## Output

Generated files follow the same convention used across the repository:

```text
results/data/      CSV field data, residual histories, and summary tables
results/figures/   generated plots
results/scaling/   OpenMP, MPI, or CUDA scaling files when available
results/logs/      optional run logs
```


## GNU Octave notes

- The same solver source is used for MATLAB and GNU Octave.
- Octave writes the same CSV summary files used by the comparison scripts.
- Octave skips figure generation by default because cluster sessions are often headless.
- To force plots in Octave, run with `OCTAVE_MAKE_FIGURES=1`.
- MATLAB users still get the normal table workflow and MATLAB `.fig` files.

## Notes

- MATLAB/Octave is the reference workflow. It contains both looped and vectorized study options.
- The maintained MATLAB workflow is under `src/` with plotting utilities in `postprocess/`.
- Root-level MATLAB files are kept only as simple compatibility entry points for people who open the folder directly in MATLAB or Octave. The maintained solver code is under `src/`.

For the full project overview, see the root `README.md`.
