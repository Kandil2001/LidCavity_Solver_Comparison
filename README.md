# Lid-Driven Cavity Solver Comparison

![MATLAB/Octave](https://img.shields.io/badge/MATLAB%2FOctave-reference-orange)
![Python](https://img.shields.io/badge/Python-serial%20%7C%20MPI-yellow)
![C](https://img.shields.io/badge/C-serial%20%7C%20OpenMP%20%7C%20MPI-blue)
![C++](https://img.shields.io/badge/C%2B%2B-serial%20%7C%20OpenMP%20%7C%20MPI-blue)
![CUDA](https://img.shields.io/badge/CUDA-GPU%20prototype-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

A solver-focused CFD/HPC benchmark for the two-dimensional incompressible lid-driven cavity problem.

The project compares the same benchmark problem across MATLAB/Octave, Python, C, C++, OpenMP, MPI, and a CUDA prototype. The goal is not to build a production CFD package. The goal is to show numerical-method implementation, code structure, validation, performance measurement, and benchmark reporting across several programming models.

## Highlights

- SIMPLE-style pressure-correction workflow for a 2D incompressible lid-driven cavity.
- Implementations in MATLAB/Octave, Python/NumPy, C, C++, OpenMP, MPI, and CUDA.
- Parameter-study benchmark over grid size, Reynolds number, convection scheme, and pressure solver.
- Runtime, residual, quality, and completion summaries.
- Representative flow-field visualizations: streamlines, velocity vectors, velocity magnitude, pressure, vorticity, residual history, and Ghia centerline validation plots.
- HPC-oriented Slurm scripts for running the benchmark on the Stromboli university cluster.

## Repository structure

```text
matlab/          MATLAB/Octave reference workflow
python/          Python serial and MPI implementations
c/               C serial, OpenMP, and MPI implementations
cpp/             C++ serial, OpenMP, and MPI implementations
cuda/            CUDA prototype
comparison/      comparison scripts, selected final tables, and report figures
docs/            project notes and reporting guides
jobs/            Slurm/HPC helper scripts
scripts/         root-level helper scripts
```

Most implementation folders follow this layout:

```text
README.md        notes for that implementation
Makefile         build/run commands
src/             solver source code
postprocess/     plotting or post-processing scripts
results/         generated local outputs, mostly ignored by Git
```

## Numerical benchmark

The benchmark is the classical lid-driven cavity flow:

- square cavity
- moving top lid
- no-slip side and bottom walls
- incompressible flow
- Reynolds-number based test cases
- centerline velocity validation against Ghia et al. benchmark data

The solver follows a SIMPLE-style pressure-correction workflow:

1. apply velocity and pressure boundary conditions
2. predict the velocity field
3. solve the pressure-correction equation
4. correct velocity and pressure
5. calculate residuals and validation metrics
6. export CSV files for comparison and plotting

## Final benchmark setup

The full CPU benchmark was run on the Stromboli university cluster using this parameter sweep:

| Parameter | Values |
|---|---|
| Grid size | `N = 32, 64, 128` |
| Reynolds number | `Re = 100, 400, 1000` |
| Convection schemes | `upwind`, `central` |
| Pressure solvers | `RBGS`, `RBSOR` |
| OpenMP setting | 4 threads |
| MPI setting | case-level parameter-study distribution |

The clean final results are stored in:

```text
comparison/results/final_clean/
```

The selected report figures are stored in:

```text
comparison/figures/report_pngs/
comparison/figures/physics_final/
comparison/figures/final_clean/
```

A more detailed result summary is available in:

```text
docs/FINAL_BENCHMARK_RESULTS.md
```

## Completion summary

| Solver group | Completed cases | Status |
|---|---:|---|
| `c_serial` | 36 / 36 | complete |
| `cpp_serial` | 36 / 36 | complete |
| `c_openmp_t4` | 36 / 36 | complete |
| `cpp_openmp_t4` | 36 / 36 | complete |
| `python_vectorized` | 36 / 36 | complete |
| `octave_vectorized` | 36 / 36 | complete |
| `c_mpi` | 36 / 36 | complete |
| `cpp_mpi` | 36 / 36 | complete |
| `python_looped` | 20 / 36 | incomplete |
| `octave_looped` | 34 / 36 | incomplete |
| `python_mpi` | 36 / 72 | incomplete |

Incomplete solvers are retained in the result tables for transparency, but the main fair ranking is based on complete solver groups.

## Runtime ranking

Median runtime over the collected cases:

| Rank | Solver group | Median runtime [s] |
|---:|---|---:|
| 1 | `c_openmp_t4` | 236.76 |
| 2 | `cpp_openmp_t4` | 284.40 |
| 3 | `c_serial` | 486.39 |
| 4 | `c_mpi` | 487.40 |
| 5 | `cpp_mpi` | 630.38 |
| 6 | `cpp_serial` | 631.80 |
| 7 | `python_vectorized` | 1941.31 |
| 8 | `octave_vectorized` | 2714.37 |

The looped Python, looped Octave, and Python MPI runs are included in the CSV summaries, but they are not used for the fair complete-solver ranking because they did not finish the full expected case set.

## Selected figures

### Runtime comparison

![Median runtime by solver](comparison/figures/report_pngs/02_median_runtime_complete_solvers_only.png)

### Ghia centerline validation, clearer low-Re benchmark case

The lower-Reynolds-number case gives the clearest visual validation against the Ghia benchmark data, so it is used here as the first validation example.

![Ghia u centerline validation](comparison/figures/physics_final/case_001_N64_Re100_central_RBSOR_openmp_cpp_ghia_u.png)

![Ghia v centerline validation](comparison/figures/physics_final/case_001_N64_Re100_central_RBSOR_openmp_cpp_ghia_v.png)

### Representative high-Re flow physics

The higher-Reynolds-number case is kept as the main physics visualization because it shows the primary cavity vortex and secondary corner structure more clearly.

![Streamlines](comparison/figures/physics_final/case_001_N128_Re1000_central_RBSOR_openmp_cpp_streamlines.png)

## Interpretation

For this benchmark, the compiled C and C++ implementations were significantly faster than the Python and Octave workflows. The fastest complete implementation was `c_openmp_t4`, followed by `cpp_openmp_t4`.

The C++ OpenMP implementation is the best practical direction for further CFD solver development because it combines strong performance with better structure and maintainability than plain C. Python remains useful for prototyping, automation, and post-processing. MPI in this repository represents case-level parameter-study parallelism, not domain decomposition.

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

## Running on Stromboli

The Stromboli helper scripts are kept in `jobs/` and `scripts/`. For a small check:

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

Cases are matched by setup, not by run order:

```text
mesh size, Reynolds number, convection scheme, pressure solver
```

## Important scope notes

### MPI

The MPI versions currently use case-level parallelism. Each MPI rank receives independent benchmark cases. This is useful for running parameter studies faster, but it is not domain decomposition yet.

### OpenMP

The OpenMP versions parallelize CPU loops inside one shared-memory process. Very small smoke cases can be slower with more threads because thread overhead dominates. Meaningful scaling should be measured on larger grids.

### CUDA

The CUDA version is a GPU prototype. It is useful for learning and comparison, but it should be compared carefully against the CPU baselines because the pressure-solver strategy is not identical to every CPU variant.

### Numerical differences

Small differences between languages are expected. The goal is not bit-for-bit identical output. The important checks are velocity fields, centerline profiles, residual trends, validation metrics, and runtime behaviour.

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
NVIDIA GPU + CUDA toolkit for CUDA
```

On Windows, WSL or a Linux-style terminal is recommended because the helper scripts and Makefiles are written for Linux/HPC-style usage.

## Good files to read first

| File | Why it matters |
|---|---|
| `docs/FINAL_BENCHMARK_RESULTS.md` | Final benchmark summary and interpretation |
| `docs/PROJECT_OVERVIEW.md` | Short numerical and project summary |
| `docs/IMPLEMENTATION_LAYOUT.md` | Standard folder layout across implementations |
| `docs/RESULTS_GUIDE.md` | Explanation of generated CSV and plot files |
| `docs/RUNNING_ON_HPC.md` | Notes for university/HPC machines |
| `docs/HOW_TO_PRESENT_THIS_PROJECT.md` | Honest wording for CV, LinkedIn, or interviews |
| `comparison/README.md` | How the comparison scripts are used |

## References

- Ghia, U., Ghia, K. N., and Shin, C. T. (1982). High-Re solutions for incompressible flow using the Navier-Stokes equations and a multigrid method. *Journal of Computational Physics*, 48(3), 387-411.
- Patankar, S. V. (1980). *Numerical Heat Transfer and Fluid Flow*. Hemisphere Publishing.
- Versteeg, H. K., and Malalasekera, W. (2007). *An Introduction to Computational Fluid Dynamics: The Finite Volume Method*. Pearson.
- Ferziger, J. H., Peric, M., and Street, R. L. (2020). *Computational Methods for Fluid Dynamics*. Springer.

## Author

Ahmed Kandil

- Email: a.akandil@outlook.com
- GitHub: [Kandil2001](https://github.com/Kandil2001)
- Portfolio: [kandil2001.github.io](https://kandil2001.github.io)
- LinkedIn: [ahmed-kandil03](https://www.linkedin.com/in/ahmed-kandil03/)

Released under the MIT License.
