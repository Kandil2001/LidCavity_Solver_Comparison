# Benchmark tracks

The repository keeps two numerical studies separate.

## Canonical domain-scaling track

The active parallel benchmark is under `src/` and uses a streamfunction–vorticity formulation.

- C and C++: OpenMP, spatial MPI, and hybrid MPI + OpenMP.
- Python: spatial MPI and hybrid MPI + threaded kernels.
- Each MPI rank owns part of one computational grid and exchanges halo values with neighboring ranks.
- Looped and vectorized kernel variants are retained as explicit implementation choices.

Performance data for this track is under `results/final/`; the small reviewed subset used in the root README is under `results/selected/`.

## Pressure-correction reference track

The earlier cross-language work remains in the top-level serial/OpenMP folders:

```text
matlab/
python/serial/
c/serial/
c/openmp/
cpp/serial/
cpp/openmp/
comparison/
```

It contains useful implementation history, residual outputs, and Ghia-profile comparisons. It is not numerically identical to the domain-scaling track, so its runtimes are not mixed with the `src/` results.

## CUDA

The CUDA implementation is experimental and stored separately. Its archived validation currently fails the configured acceptance thresholds, so it is excluded from headline performance claims.

## Removed workflow

MPI parameter-sweep scheduling was removed. MPI in this repository now means spatial decomposition of one CFD grid.
