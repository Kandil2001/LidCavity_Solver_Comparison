# CUDA Solver

**Role:** Single-GPU prototype  
**Language/platform:** CUDA C++

This folder contains the NVIDIA CUDA version. It is intended for GPU machines and is kept separate from the normal CPU workflow because it requires both the CUDA toolkit and an accessible NVIDIA GPU.

## What this CUDA version is

The CUDA solver is a GPU prototype for the same lid-driven cavity benchmark. It is useful for learning, comparison, and basic GPU performance testing. It should not be oversold as identical to every CPU solver variant because the pressure correction uses a GPU-friendly Jacobi-style iteration.

## Check CUDA availability

```bash
make check-cuda
```

This checks for:

```text
nvcc
nvidia-smi
an accessible NVIDIA GPU
```

On a CPU-only login node, this check will fail and the CUDA run should be skipped or moved to a GPU node.

## Run

```bash
make smoke
make quick
make run N=64 RE=100 SCHEME=upwind PRESSURE=JACOBI
```

The run modes are:

| Mode | Purpose |
|---|---|
| `smoke` | tiny GPU check, no field output |
| `quick` | small GPU benchmark, no field output |
| `medium` | larger GPU run |
| `full` | longer GPU run |

## CUDA performance sweep

```bash
make scaling
```

or from the repository root:

```bash
make scaling-cuda
```

This runs a block-size performance sweep and writes:

```text
cuda/results/scaling/cuda_block_size_scaling.csv
comparison/results/figures/scaling/
```

This is **GPU tuning**, not the same as OpenMP strong scaling or MPI case-level scaling.

## Folder layout

| Path | Purpose |
|---|---|
| `Makefile` | CUDA build/run/scaling commands |
| `src/lid_cavity_cuda.cu` | Single translation-unit entry file |
| `src/app/` | CLI, config, and main loop |
| `src/common/` | CUDA utility helpers |
| `src/kernels/` | GPU kernels |
| `src/post/` | CSV output |
| `postprocess/` | Scaling plotting scripts |
| `results/` | Generated CSV, figures, scaling, and logs |
| `requirements.txt` | Python dependencies for plotting |

## Notes for Stromboli

From the repository root, the Stromboli helper includes CUDA automatically when it detects `nvcc` and a usable NVIDIA GPU:

```bash
bash scripts/run_stromboli_all.sh smoke
```

To skip CUDA explicitly:

```bash
RUN_CUDA=0 bash scripts/run_stromboli_all.sh smoke
```

For the full project overview, see the root `README.md`.
