# Lid-Driven Cavity Solver Comparison

![MATLAB](https://img.shields.io/badge/MATLAB-reference-orange)
![Python](https://img.shields.io/badge/Python-serial%20%7C%20MPI-yellow)
![C](https://img.shields.io/badge/C-serial%20%7C%20OpenMP%20%7C%20MPI-blue)
![C++](https://img.shields.io/badge/C%2B%2B-serial%20%7C%20OpenMP%20%7C%20MPI-blue)
![CUDA](https://img.shields.io/badge/CUDA-NVIDIA%20GPU-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

A clean comparison project for the 2D incompressible lid-driven cavity benchmark.

The same CFD problem is solved in MATLAB, Python, C, C++, OpenMP, MPI, and CUDA. The goal is to keep the numerical setup as consistent as possible, then compare implementation style, runtime, residual behaviour, validation error, and output structure.

This repository is not a commercial CFD solver. It is a portfolio-style benchmark that shows how a simple numerical method can grow from a clear reference implementation into faster CPU and GPU versions.

## At a glance

| Part | What it shows |
|---|---|
| MATLAB | Reference workflow and validation baseline |
| Python | Readable implementation and post-processing-friendly structure |
| C | Low-level serial CPU baseline |
| C++ | Cleaner compiled-code baseline |
| OpenMP | Shared-memory CPU parallelism |
| MPI | Case-level parallel runs for parameter studies |
| CUDA | GPU implementation for NVIDIA machines |
| Comparison tools | Side-by-side CSV reports and plots |

## What is included

- MATLAB reference workflow with looped and vectorized parts
- Python serial solver
- Python MPI case runner
- C serial solver
- C OpenMP solver
- C MPI case runner
- C++ serial solver
- C++ OpenMP solver
- C++ MPI case runner
- CUDA solver for NVIDIA GPUs
- Root helper scripts for smoke and quick CPU checks
- Comparison scripts for matching finished cases across implementations
- Short documentation for results, HPC usage, and project structure

## Repository structure

```text
matlab/          MATLAB reference implementation
python/          Python serial and MPI implementations
c/               C serial, OpenMP, and MPI implementations
cpp/             C++ serial, OpenMP, and MPI implementations
cuda/            CUDA implementation for NVIDIA GPUs
comparison/      comparison and reporting scripts
docs/            project notes and running guides
scripts/         root-level helper scripts
```

Each solver folder is kept close to a standalone mini-repository. This makes the main repo useful as a comparison hub while still allowing each implementation to be moved into its own GitHub repo later.

## Implementations

| Folder | Implementation | Main use |
|---|---|---|
| `matlab/` | MATLAB | Reference workflow, validation, plotting |
| `python/serial/` | Python / NumPy | Readable serial implementation |
| `python/mpi/` | Python + MPI | Case-level parallel benchmark runner |
| `c/serial/` | C | Low-level serial CPU baseline |
| `c/openmp/` | C + OpenMP | Shared-memory CPU scaling |
| `c/mpi/` | C + MPI | Case-level parallel benchmark runner |
| `cpp/serial/` | C++ | Structured compiled-code baseline |
| `cpp/openmp/` | C++ + OpenMP | Shared-memory CPU scaling |
| `cpp/mpi/` | C++ + MPI | Case-level parallel benchmark runner |
| `cuda/` | CUDA C++ | NVIDIA GPU version |
| `comparison/` | Python scripts | Compare summaries, runtimes, and validation metrics |

## Numerical benchmark

The benchmark is the classical lid-driven cavity flow:

- square cavity
- moving top lid
- no-slip side and bottom walls
- incompressible flow
- Reynolds-number based comparison cases
- velocity centerline validation against Ghia et al. data

The solver follows a SIMPLE-style pressure-correction workflow:

1. set velocity and pressure boundary conditions
2. predict the velocity field
3. solve the pressure-correction equation
4. correct velocity and pressure
5. calculate residuals and validation metrics
6. export CSV files for comparison

## Quick start

From the repository root:

```bash
make help
make smoke-cpu
```

`smoke-cpu` is the safest first command. It runs small checks and skips optional tools that are not installed.

For a larger CPU run:

```bash
make quick-cpu
```

To run one implementation directly:

```bash
cd cpp/serial
make quick
```

For OpenMP:

```bash
cd cpp/openmp
make quick OMP_NUM_THREADS=4
```

For MPI:

```bash
cd c/mpi
make quick NP=4
```

For CUDA, use a machine with an NVIDIA GPU and CUDA toolkit:

```bash
cd cuda
make smoke
```

## Run modes

| Mode | Meaning |
|---|---|
| `smoke` | Very small test to check that the code builds and starts correctly |
| `quick` | Small benchmark run for fast checking |
| `medium` | Larger MATLAB run with more cases |
| `full` | Full benchmark study, intended for longer runs |
| `single` | One selected case from the command line |

Example single case:

```bash
cd c/serial
make run N=128 RE=400 SCHEME=upwind PRESSURE=RBGS
```

## Output files

Each implementation writes generated files inside its own folder:

```text
results/data/      summary CSV files, field CSV files, residual histories
results/figures/   generated plots
results/scaling/   scaling tables for OpenMP, MPI, or CUDA when available
```

Generated result folders are mostly ignored by Git. This keeps the repository clean and avoids uploading large temporary outputs.

## Comparing results

After running the serial implementations, create a comparison from the root:

```bash
make compare-serial MODE=quick
make report-serial MODE=quick
```

The comparison output is written to:

```text
comparison/results/
```

Cases are matched by setup, not by run order. The matching keys are:

```text
mesh size, Reynolds number, convection scheme, pressure solver
```

## What to look at first

For a quick review of the project, open these files first:

| File | Why it matters |
|---|---|
| `README.md` | Main project explanation |
| `docs/PROJECT_OVERVIEW.md` | Short numerical and project overview |
| `docs/RESULTS_GUIDE.md` | Explains generated CSV and plot files |
| `docs/RUNNING_ON_HPC.md` | Notes for running on university machines |
| `comparison/README.md` | How the comparison scripts are used |

## Requirements

Basic CPU runs need:

```text
gcc / g++
make
python3
```

Python plotting and comparison packages:

```bash
python3 -m pip install -r requirements.txt
```

MATLAB folder:

```text
MATLAB with batch mode support
```

MPI folders:

```text
OpenMPI or another MPI implementation
mpicc / mpicxx / mpirun
mpi4py for Python MPI
```

CUDA folder:

```text
NVIDIA GPU
CUDA toolkit
nvcc
```

On Windows, WSL or a Linux-style terminal is recommended because the helper scripts and Makefiles are written for Linux/HPC-style usage.

## Important notes

### MPI

The MPI versions currently use case-level parallelism. Each MPI rank receives independent benchmark cases. This is useful for running a parameter study faster, but it is not domain decomposition yet.

### CUDA

The CUDA version needs an NVIDIA GPU and CUDA toolkit. On a CPU-only university machine, skip the `cuda/` folder and use the CPU solvers.

### Numerical differences

Small differences between languages are expected. The goal is not bit-for-bit identical output. The important checks are velocity fields, centerline profiles, residual trends, validation error, and runtime behaviour.

## Current status

The repository is prepared as a clean comparison hub. The next practical step is to run the full benchmark set on the university machine, then add selected final plots and tables to this README.

## Roadmap

- Add final benchmark tables after the full run is complete
- Add selected velocity, residual, validation, and runtime plots
- Compare MATLAB, Python, C, and C++ serial results first
- Add OpenMP scaling discussion
- Add MPI case-parallel scaling discussion
- Run CUDA only on a GPU machine
- Add OpenFOAM and LBM follow-up repositories later

## Reference

Ghia, U., Ghia, K. N., and Shin, C. T. (1982). *High-Re solutions for incompressible flow using the Navier-Stokes equations and a multigrid method*. Journal of Computational Physics, 48(3), 387-411.

## Author

Ahmed Kandil

Released under the MIT License.
