# CUDA solver

This folder contains the NVIDIA GPU version of the lid-driven cavity solver.

Only build this folder on a machine with an NVIDIA GPU and the CUDA toolkit.

## Check the machine

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

If `nvidia-smi` or `nvcc` is missing, skip this folder and run the CPU solvers instead.
