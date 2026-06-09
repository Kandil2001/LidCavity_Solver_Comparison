# Lid-Driven Cavity Solver Comparison

![MATLAB](https://img.shields.io/badge/MATLAB-reference-orange)
![Python](https://img.shields.io/badge/Python-serial%20%7C%20MPI-yellow)
![C](https://img.shields.io/badge/C-serial%20%7C%20OpenMP%20%7C%20MPI-blue)
![C++](https://img.shields.io/badge/C%2B%2B-serial%20%7C%20OpenMP%20%7C%20MPI-blue)
![CUDA](https://img.shields.io/badge/CUDA-NVIDIA%20GPU-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

A clean multi-platform CFD benchmark for the two-dimensional incompressible lid-driven cavity problem.

The same numerical problem is solved in MATLAB, Python, C, C++, OpenMP, MPI, and CUDA. The aim is not to build a commercial CFD package, but to show the same solver idea moving from a readable reference workflow to faster CPU, parallel, and GPU implementations.

## Project idea

The repository is built around one benchmark and one comparison philosophy:

> Keep the physical setup as consistent as possible, then compare implementation style, runtime, convergence behaviour, validation error, and output structure.

The project is useful as a CFD learning project, a numerical-methods portfolio piece, and a starting point for later OpenFOAM, LBM, or domain-decomposition projects.

## At a glance

| Part | What it shows |
|---|---|
| MATLAB | Reference workflow, looped and vectorized cases, validation baseline |
| Python | Readable implementation and post-processing-friendly code |
| C | Low-level serial CPU baseline |
| C++ | Structured compiled-code baseline |
| OpenMP | Shared-memory CPU parallelism |
| MPI | Case-level parallel parameter studies |
| CUDA | NVIDIA GPU prototype |
| Comparison tools | Side-by-side CSV reports and plots |

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

Each implementation follows the same general layout:

```text
README.md        explains that implementation
Makefile         common build/run commands
src/             solver source code
postprocess/     plotting or post-processing scripts
results/         generated outputs, mostly ignored by Git
```

The result folders are also consistent:

```text
results/data/      CSV summaries, field data, residual histories
results/figures/   generated plots
results/scaling/   OpenMP, MPI, or CUDA scaling tables
results/logs/      optional logs from long runs
```

## Implementations

| Folder | Implementation | Main use |
|---|---|---|
| `matlab/` | MATLAB | Reference workflow, validation, and plotting |
| `python/serial/` | Python / NumPy | Readable serial implementation |
| `python/mpi/` | Python + mpi4py | Case-level MPI benchmark runner |
| `c/serial/` | C | Low-level serial CPU baseline |
| `c/openmp/` | C + OpenMP | Shared-memory CPU scaling |
| `c/mpi/` | C + MPI | Case-level MPI benchmark runner |
| `cpp/serial/` | C++ | Structured compiled-code baseline |
| `cpp/openmp/` | C++ + OpenMP | Shared-memory CPU scaling |
| `cpp/mpi/` | C++ + MPI | Case-level MPI benchmark runner |
| `cuda/` | CUDA C++ | NVIDIA GPU prototype |
| `comparison/` | Python scripts | Compare summaries, runtimes, and validation metrics |

## Numerical benchmark

The benchmark is the classical lid-driven cavity flow:

- square cavity
- moving top lid
- no-slip side and bottom walls
- incompressible flow
- Reynolds-number based comparison cases
- velocity centerline validation against the Ghia et al. benchmark data

The solver follows a SIMPLE-style pressure-correction workflow:

1. apply velocity and pressure boundary conditions
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

`smoke-cpu` is the safest first command. It runs small CPU checks and skips optional tools that are not installed.

For a larger CPU run:

```bash
make quick-cpu
```

Run one implementation directly:

```bash
cd cpp/serial
make quick
```

Run an OpenMP version:

```bash
cd cpp/openmp
make quick OMP_NUM_THREADS=4
```

Run an MPI version on a machine with MPI installed:

```bash
cd c/mpi
make quick NP=4
```

Run CUDA on a machine with an NVIDIA GPU and CUDA toolkit:

```bash
cd cuda
make smoke
```

## Run modes

| Mode | Meaning |
|---|---|
| `smoke` | Very small test to check that the code builds and starts correctly |
| `quick` | Small benchmark run for fast checking |
| `medium` | Larger check with more cases |
| `full` | Full benchmark study, intended for longer runs |
| `single` | One selected case from the command line |

Example single case:

```bash
cd c/serial
make run N=128 RE=400 SCHEME=upwind PRESSURE=RBGS
```

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

| File | Why it matters |
|---|---|
| `README.md` | Main project overview |
| `docs/PROJECT_OVERVIEW.md` | Numerical and project summary |
| `docs/IMPLEMENTATION_LAYOUT.md` | Standard folder layout across implementations |
| `docs/RESULTS_GUIDE.md` | Explanation of generated CSV and plot files |
| `docs/RUNNING_ON_HPC.md` | Notes for running on university/HPC machines |
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

The CUDA version needs an NVIDIA GPU and CUDA toolkit. On a CPU-only machine, skip the `cuda/` folder and use the CPU solvers.

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
- Run CUDA on a GPU machine
- Add OpenFOAM and LBM follow-up repositories later

## References

- Ghia, U., Ghia, K. N., and Shin, C. T. (1982). *High-Re solutions for incompressible flow using the Navier-Stokes equations and a multigrid method*. Journal of Computational Physics, 48(3), 387-411.
- Patankar, S. V. (1980). *Numerical Heat Transfer and Fluid Flow*. Hemisphere Publishing.
- Versteeg, H. K., and Malalasekera, W. (2007). *An Introduction to Computational Fluid Dynamics: The Finite Volume Method*. Pearson.
- Ferziger, J. H., Peric, M., and Street, R. L. (2020). *Computational Methods for Fluid Dynamics*. Springer.

## Author

**Ahmed Kandil**

- Email: kandil.ahmed.amr@gmail.com
- GitHub: Kandil2001
- Portfolio: kandil2001.github.io
- LinkedIn: ahmed-kandil03

Released under the MIT License.
