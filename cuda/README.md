# CUDA Solver

**Role in the project:** NVIDIA GPU implementation.

This folder contains the CUDA version of the lid-driven cavity solver. It should only be built on a machine with an NVIDIA GPU and the CUDA toolkit.

If the machine has no CUDA support, skip this folder. The CPU solvers can still be run normally.

## Requirements

```text
NVIDIA GPU
CUDA toolkit
nvcc
```

Check the machine:

```bash
nvidia-smi
nvcc --version
```

## Build and run

```bash
make build
make smoke
make run N=128 RE=400 MAX_ITER=500 POISSON_ITER=300
```

Direct command example:

```bash
./bin/lid_cavity_cuda --N 128 --Re 400 --scheme upwind --maxIter 500 --poisson-maxIter 300
```

## Output

```text
results/data/      CSV summaries and field data
results/figures/   generated plots when available
```

## Notes

- CUDA is separate because it needs a different compiler and hardware.
- Do not expect this folder to run on normal CPU-only university PCs.
- Compare CUDA timing only with cases that use the same numerical setup.
