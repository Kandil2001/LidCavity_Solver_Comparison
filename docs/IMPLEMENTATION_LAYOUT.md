# Implementation layout

The repository contains an original cross-language solver tree and a later organized domain-scaling source tree. These are related projects, but they currently use different numerical formulations.

See [`BENCHMARK_TRACKS.md`](BENCHMARK_TRACKS.md) before moving code or comparing results.

## Track A — original pressure-correction implementations

The root-level implementation folders are the canonical source for the original cross-language workflow:

```text
matlab/
python/serial/
python/mpi/
c/serial/
c/openmp/
c/mpi/
cpp/serial/
cpp/openmp/
cpp/mpi/
cuda/
```

Most folders follow:

```text
README.md        implementation notes and commands
Makefile         build and run commands
src/             solver source code
postprocess/     plotting and post-processing scripts
results/         generated outputs
```

The original `python/mpi`, `c/mpi`, and `cpp/mpi` implementations distribute independent cases over MPI ranks. They are not spatial domain-decomposition solvers.

## Track B — organized domain-scaling source tree

The later streamfunction–vorticity implementations are stored under `src/`:

```text
src/c/
src/cpp/
src/python/
```

This tree contains implementation families such as:

```text
openmp_domain_looped/
openmp_domain_vectorized/
mpi_domain_looped/
mpi_domain_vectorized/
hybrid_mpi_openmp_looped/
hybrid_mpi_openmp_vectorized/
```

Run and Slurm scripts for this track must reference the `src/...` paths. Older paths such as `c/mpi_domain_looped` or `cpp/openmp_domain_vectorized` refer to the pre-organization layout and should not be introduced into new scripts.

The associated case definitions, HPC scripts, and archived results are stored under:

```text
data/cases/
hpc/stromboli/
results/final/
results/audits/
```

## Standard result structure

Implementation-local generated outputs generally use:

```text
results/data/      CSV summaries and field data
results/figures/   generated plots
results/scaling/   scaling tables
results/logs/      run logs
```

Repository-level retained archives are intentionally separate:

```text
comparison/results/   pressure-correction pilot results
comparison/figures/   pressure-correction pilot figures
results/final/        streamfunction–vorticity scaling archive
results/cuda/         CUDA summaries and validation tables
```

## MATLAB note

The maintained MATLAB pressure-correction source is under `matlab/src/`. Root-level MATLAB entry files are compatibility wrappers for direct use of the `matlab/` folder.

## C and C++ naming note

In the original pressure-correction track, the C and C++ serial/OpenMP implementations are single compiled baselines. Older labels that contain `looped` or `vectorized` may be accepted as aliases, but they do not represent separate numerical algorithms.

In the domain-scaling track, `looped` and `vectorized` identify distinct kernel organizations and must remain explicit in result tables.

## Path policy

- Use root-level `c/`, `cpp/`, and `python/` for the original pressure-correction workflow.
- Use `src/c/`, `src/cpp/`, and `src/python/` for the streamfunction–vorticity domain workflow.
- Do not silently copy or mix implementations between tracks.
- Every result-processing script must state which track it expects.
