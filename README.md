# Lid-driven cavity solver comparison

This repository is a small CFD learning project built around one classic benchmark: the 2D lid-driven cavity.

The idea is simple: solve the same problem several times, using different languages and parallel-programming approaches, then compare the runtime, residuals, validation error, and code structure.

I started from a MATLAB workflow and then rebuilt the same benchmark in Python, C, C++, OpenMP, MPI, and CUDA. The project is not meant to be a commercial CFD package. It is meant to show how a numerical solver grows from a clear reference version into faster and more parallel versions.

## What this repo shows

- A SIMPLE-style incompressible-flow solver for the lid-driven cavity.
- MATLAB looped and vectorized reference workflows.
- Python implementation for readability and post-processing.
- C and C++ serial CPU implementations.
- OpenMP versions for shared-memory CPU parallelism.
- MPI versions that distribute independent benchmark cases across ranks.
- A CUDA version for NVIDIA GPU machines.
- Scripts for comparing finished CSV outputs.

## Repository layout

```text
matlab/          MATLAB reference implementation
python/serial/  serial Python / NumPy implementation
python/mpi/     Python MPI case-parallel runner
c/serial/       serial C implementation
c/openmp/       C implementation with OpenMP
c/mpi/          C MPI case-parallel runner
cpp/serial/     serial C++ implementation
cpp/openmp/     C++ implementation with OpenMP
cpp/mpi/        C++ MPI case-parallel runner
cuda/           CUDA implementation for NVIDIA GPUs
comparison/     comparison and reporting scripts
docs/           short project notes
scripts/        root helper scripts
```

Each solver folder can still be used on its own. The root scripts are only there to make testing the whole repository easier.

## Quick start

From the repository root:

```bash
make help
make smoke-cpu
```

`smoke-cpu` runs the smallest CPU checks and skips tools that are not installed on the machine. This is the safest first command after cloning the repo.

For a larger CPU run:

```bash
make quick-cpu
```

You can also run one implementation directly:

```bash
cd cpp/serial
make quick
```

or with OpenMP:

```bash
cd cpp/openmp
make quick OMP_NUM_THREADS=4
```

## Run modes

The implementations use the same mode names where possible:

| Mode | Purpose |
|---|---|
| `smoke` | Very small check. Good for testing the build. |
| `quick` | Small benchmark run. Good before committing results. |
| `medium` | Larger check with more Reynolds numbers. |
| `full` | Full benchmark grid. Can take much longer. |
| `single` | One chosen case from the command line. |

Example single case:

```bash
cd c/serial
make run N=128 RE=400 SCHEME=upwind PRESSURE=RBGS
```

## Output files

Generated results are written inside each implementation folder:

```text
results/data/      summary CSV files, field CSV files, residual histories
results/figures/   generated plots
results/scaling/   OpenMP/MPI/CUDA scaling CSV files where available
```

These outputs are ignored by Git by default. Keep only selected final figures or reports if you want to show results on GitHub.

## Comparing results

After running the serial implementations, create a comparison table from the root:

```bash
make compare-serial MODE=quick
make report-serial MODE=quick
```

This writes the final comparison files to:

```text
comparison/results/
```

The comparison is based on the physical and numerical setup, not on the case number. It matches cases using:

```text
N, Re, numerical scheme, pressure solver
```

## Important notes

### MPI

The MPI versions currently use case-level parallelism. That means each MPI rank receives independent benchmark cases. This is useful for running a study faster, but it is not a domain-decomposition CFD solver yet.

### CUDA

The CUDA folder requires an NVIDIA GPU and the CUDA toolkit. On a normal CPU-only university PC, use the MATLAB, Python, C, C++, OpenMP, and MPI folders and leave CUDA for a GPU machine.

### Numerical differences

Small differences between languages are expected. The solvers do not need to be bit-for-bit identical. What matters is whether the fields, centerline profiles, residuals, Ghia validation metrics, and trends are consistent.

## Validation reference

The velocity centerline validation is based on the standard lid-driven cavity data from:

Ghia, U., Ghia, K. N., and Shin, C. T. (1982). *High-Re solutions for incompressible flow using the Navier-Stokes equations and a multigrid method*. Journal of Computational Physics, 48(3), 387–411.

## Roadmap

- Add checked benchmark results after the full runs are complete.
- Add selected plots to the README once the final comparison is stable.
- Extend MPI from case-level parallelism toward domain decomposition.
- Add OpenFOAM and LBM projects as separate follow-up comparisons.
