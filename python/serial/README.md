# Python Serial Solver

**Role:** Readable serial implementation  
**Language/platform:** Python / NumPy

This folder contains the serial Python implementation. It is useful for readable code, quick checks, and post-processing-friendly CSV output.

## Run

```bash
make smoke
make quick
```

## Single case example

```bash
make run N=64 RE=100 SCHEME=central PRESSURE=RBGS
```

## Folder layout

| Path | Purpose |
|---|---|
| `Makefile` | Common run commands |
| `src/lid_cavity.py` | Command-line entry point |
| `src/lidcavity/` | Python package with config, operators, solver, IO, and validation |
| `postprocess/` | Plotting scripts |
| `results/` | Generated CSV, figures, scaling, and logs |
| `requirements.txt` | Python dependencies |

## Output

Generated files follow the same convention used across the repository:

```text
results/data/      CSV field data, residual histories, and summary tables
results/figures/   generated plots
results/scaling/   OpenMP, MPI, or CUDA scaling files when available
results/logs/      optional run logs
```


## Notes

- Use this version when readability matters more than maximum speed.

For the full project overview, see the root `README.md`.
