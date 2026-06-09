# CUDA Solver

**Role:** Single-GPU prototype  
**Language/platform:** CUDA C++

This folder contains the NVIDIA CUDA version. It is intended for GPU machines and is kept separate from the CPU smoke workflow.

## Run

```bash
make smoke
make run N=64 RE=100
```

## Single case example

```bash
make run N=64 RE=100 SCHEME=upwind MAX_ITER=500 POISSON_ITER=300
```

## Folder layout

| Path | Purpose |
|---|---|
| `Makefile` | CUDA build and run commands |
| `src/lid_cavity_cuda.cu` | Single translation-unit entry file |
| `src/app/` | CLI, config, and main loop |
| `src/common/` | CUDA utility helpers |
| `src/kernels/` | GPU kernels |
| `src/post/` | CSV output |
| `postprocess/` | Scaling plotting scripts |
| `results/` | Generated CSV, figures, scaling, and logs |

## Output

Generated files follow the same convention used across the repository:

```text
results/data/      CSV field data, residual histories, and summary tables
results/figures/   generated plots
results/scaling/   OpenMP, MPI, or CUDA scaling files when available
results/logs/      optional run logs
```

## Notes

- Requires an NVIDIA GPU, CUDA toolkit, and `nvcc`.
- The CUDA solver is a GPU prototype and should be compared carefully against the CPU baselines.

For the full project overview, see the root `README.md`.
