# Lid-Driven Cavity Solver Comparison

![MATLAB/Octave](https://img.shields.io/badge/MATLAB%2FOctave-reference-orange)
![Python](https://img.shields.io/badge/Python-serial%20%7C%20MPI-yellow)
![C](https://img.shields.io/badge/C-serial%20%7C%20OpenMP%20%7C%20MPI-blue)
![C++](https://img.shields.io/badge/C%2B%2B-serial%20%7C%20OpenMP%20%7C%20MPI-blue)
![CUDA](https://img.shields.io/badge/CUDA-GPU%20prototype-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

A solver-focused CFD benchmark for the two-dimensional incompressible lid-driven cavity problem.

The goal is simple: keep the physical setup as consistent as possible, then compare how the same CFD problem behaves when it is implemented in MATLAB, Python, C, C++, OpenMP, MPI, and CUDA. This is not meant to be a commercial CFD solver. It is a portfolio and learning project for numerical methods, code structure, validation, and benchmark reporting.

## What this project shows

| Part | Role in the project |
|---|---|
| MATLAB/Octave | Reference workflow with looped and vectorized study options |
| Python | Readable NumPy implementation plus a loop-style baseline |
| C | Compiled serial CPU baseline |
| C++ | Structured compiled-code baseline |
| OpenMP | Shared-memory CPU threading for C and C++ |
| MPI | Case-level parallel parameter studies |
| CUDA | Single-GPU prototype |
| Comparison tools | CSV matching, grid-convergence tables, validation plots, scaling plots, and reports |

## Repository structure

```text
matlab/          MATLAB/Octave reference implementation
python/          Python serial and MPI implementations
c/               C serial, OpenMP, and MPI implementations
cpp/             C++ serial, OpenMP, and MPI implementations
cuda/            CUDA implementation for NVIDIA GPUs
comparison/      comparison and reporting scripts
docs/            project notes and running guides
scripts/         root-level helper scripts
```

Most implementation folders follow the same layout:

```text
README.md        explains that implementation
Makefile         common build/run commands
src/             solver source code
postprocess/     plotting or post-processing scripts
results/         generated outputs, mostly ignored by Git
```

## Numerical benchmark

The benchmark is the classical lid-driven cavity flow:

- square cavity
- moving top lid
- no-slip side and bottom walls
- incompressible flow
- Reynolds-number based test cases
- centerline velocity validation against the Ghia et al. benchmark data

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



## Running on Stromboli

The easiest Stromboli entry point is the all-in-one helper. It checks the available compilers/tools first, then runs only the parts that can actually run on that node. CUDA is included when `nvcc` and an accessible NVIDIA GPU are available.

```bash
bash scripts/run_stromboli_all.sh smoke
# or
make smoke-stromboli
```

For a longer run that survives a dropped SSH connection:

```bash
nohup bash scripts/run_stromboli_all.sh quick > stromboli_quick.log 2>&1 &
tail -f stromboli_quick.log
```

To intentionally skip CUDA on a CPU-only login node:

```bash
RUN_CUDA=0 bash scripts/run_stromboli_all.sh quick
```

If CUDA is available on a different GPU node, run the CUDA folder there:

```bash
cd cuda
make check-cuda
make smoke
make scaling
```

## Running the reference solver with GNU Octave

The `matlab/` folder is now MATLAB/Octave-compatible. MATLAB is still supported, but on a university cluster such as Stromboli you can force GNU Octave:

```bash
cd matlab
make smoke ENGINE=octave
make quick ENGINE=octave
```

From the repository root, this also works:

```bash
ENGINE=octave make smoke-cpu
ENGINE=octave make quick-cpu
```

There is also a Stromboli helper script:

```bash
bash scripts/run_stromboli_octave.sh smoke
bash scripts/run_stromboli_octave.sh quick
```

For longer cluster runs:

```bash
nohup bash scripts/run_stromboli_octave.sh quick > octave_quick.log 2>&1 &
tail -f octave_quick.log
```

By default, Octave runs skip figure generation because many cluster sessions are headless. The solver still writes CSV and `.mat` outputs. To force Octave figures, use:

```bash
OCTAVE_MAKE_FIGURES=1 bash scripts/run_stromboli_octave.sh quick
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

Cases are matched by setup, not by run order:

```text
mesh size, Reynolds number, convection scheme, pressure solver
```


## Automated studies and plots

Run a grid-convergence study from the repository root:

```bash
make grid-convergence
```

The default command runs the C++ serial solver for `N=32,64,128` at `Re=100` and writes:

```text
comparison/results/grid_convergence/
```

You can also call the script directly, for example:

```bash
python3 scripts/run_grid_convergence.py --solver cpp --N-list 32,64,128 --Re 100 --scheme upwind --pressure RBGS
python3 scripts/run_grid_convergence.py --solver python --implementation serial_python_vectorized --N-list 32,64
```

The observed order is calculated from the Ghia centerline L2 errors. This is useful for a portfolio benchmark, but it should be described as a benchmark-data convergence check, not a manufactured-solution proof.

Create automatic U/V centerline validation plots against the Ghia data:

```bash
make validation-plots
python3 scripts/plot_validation_centerlines.py --Re 100 --N 64 --scheme upwind --pressure RBGS
```

The plots are written to:

```text
comparison/results/figures/validation/
```

Run OpenMP, MPI, or CUDA scaling/performance checks:

```bash
make scaling-openmp
make scaling-mpi MODE=quick
make scaling-cuda
make scaling-all MODE=quick
```

OpenMP scaling is strong scaling for one fixed CPU case. MPI scaling is case-level scaling for a parameter sweep, not domain decomposition. CUDA uses a block-size performance sweep for the GPU prototype, so it should be presented as GPU tuning rather than classical strong scaling. The scaling CSV and plots are written under:

```text
comparison/results/scaling/
comparison/results/figures/scaling/
```

## Important scope notes

### C labels

C is kept as one compiled serial baseline. Older output labels such as `serial_c_looped` or `serial_c_vectorized` are accepted only for backward compatibility. They do not represent two different C algorithms.

### OpenMP, MPI, and looped/vectorized labels

Do not describe every OpenMP/MPI solver as having both looped and vectorized versions. The honest split is:

| Solver family | Looped/vectorized status |
|---|---|
| MATLAB/Octave | Reference workflow keeps loop-style and vectorized study options |
| Python serial | Has NumPy/vectorized-style and loop-style implementations |
| Python MPI | Distributes the Python case list, so it can run both Python implementation labels |
| C serial | One compiled baseline only |
| C OpenMP | One threaded C baseline only |
| C MPI | One case-parallel C baseline only |
| C++ serial | One compiled C++ baseline only |
| C++ OpenMP | One threaded C++ baseline only |
| C++ MPI | One case-parallel C++ baseline only |

The compiler may auto-vectorize some C/C++ loops with optimization flags, but that is not the same as maintaining a separate vectorized algorithm.

### MPI

The MPI versions currently use case-level parallelism. Each MPI rank receives independent benchmark cases. This is useful for running parameter studies faster, but it is not domain decomposition yet.

### OpenMP

The OpenMP versions parallelize CPU loops inside one shared-memory process. Very small smoke cases can be slower with more threads because thread overhead dominates. Meaningful scaling should be measured on larger grids.

### CUDA

The CUDA version is a GPU prototype. It is useful for learning and comparison, but it should be compared carefully against the CPU baselines because the pressure-solver strategy is not identical to every CPU variant.

### Numerical differences

Small differences between languages are expected. The goal is not bit-for-bit identical output. The important checks are velocity fields, centerline profiles, residual trends, validation error, and runtime behaviour.

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

Optional tools:

```text
MATLAB with batch mode support, or GNU Octave for the reference solver
OpenMPI or another MPI implementation
mpi4py for Python MPI
NVIDIA GPU + CUDA toolkit for CUDA. On CPU-only nodes, CUDA commands are skipped by `scripts/run_stromboli_all.sh`.
```

On Windows, WSL or a Linux-style terminal is recommended because the helper scripts and Makefiles are written for Linux/HPC-style usage.

## Good files to read first

| File | Why it matters |
|---|---|
| `docs/PROJECT_OVERVIEW.md` | Short numerical and project summary |
| `docs/IMPLEMENTATION_LAYOUT.md` | Standard folder layout across implementations |
| `docs/RESULTS_GUIDE.md` | Explanation of generated CSV and plot files |
| `docs/RUNNING_ON_HPC.md` | Notes for university/HPC machines |
| `docs/HOW_TO_PRESENT_THIS_PROJECT.md` | Honest wording for CV, LinkedIn, or interviews |
| `comparison/README.md` | How the comparison scripts are used |

## Current status

The repository is prepared as a clean comparison hub. The next practical step is to run the full benchmark set on the university machine, then add a small number of selected final plots and tables to this README.

## Roadmap

- Run the full benchmark on a stronger machine
- Add one selected runtime table
- Add one validation table
- Add one residual plot
- Add one velocity or streamline plot
- Add OpenMP and MPI scaling discussion
- Add later extensions such as LBM or OpenFOAM as separate projects
