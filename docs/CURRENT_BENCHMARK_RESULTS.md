# Current benchmark results

> **Project status:** Work in progress. This document records the evidence currently retained in the repository. It is not a frozen final benchmark or paper dataset.

The repository contains two numerically different tracks. See [`BENCHMARK_TRACKS.md`](BENCHMARK_TRACKS.md) before interpreting or combining results.

## 1. Pressure-correction cross-language pilot

### Matrix

| Parameter | Values |
|---|---|
| Grid size | `N = 32, 64, 128` |
| Reynolds number | `Re = 100, 400, 1000` |
| Convection | `upwind`, `central` |
| Pressure solver | `RBGS`, `RBSOR` |
| OpenMP setting | 4 threads in the cleaned pilot export |
| Original MPI setting | independent cases distributed across ranks |

Retained files:

```text
comparison/results/final_clean/
comparison/results/physics_fields/
comparison/figures/report_pngs/
comparison/figures/physics_final/
```

### Execution completeness

| Solver group | Executed cases | Status |
|---|---:|---|
| `c_serial` | 36 / 36 | execution-complete |
| `cpp_serial` | 36 / 36 | execution-complete |
| `c_openmp_t4` | 36 / 36 | execution-complete |
| `cpp_openmp_t4` | 36 / 36 | execution-complete |
| `python_vectorized` | 36 / 36 | execution-complete |
| `octave_vectorized` | 36 / 36 | execution-complete |
| `c_mpi` | 36 / 36 | execution-complete |
| `cpp_mpi` | 36 / 36 | execution-complete |
| `python_looped` | 20 / 36 | incomplete |
| `octave_looped` | 34 / 36 | incomplete |
| `python_mpi` | 36 / 72 | incomplete |

Execution-complete means that the configured run ended and a result row was produced. It does not automatically mean that the numerical solution converged.

### Interim execution-time summary

Median runtime over the collected rows:

| Rank | Solver group | Rows | Median runtime [s] |
|---:|---|---:|---:|
| 1 | `c_openmp_t4` | 36 | 236.76 |
| 2 | `cpp_openmp_t4` | 36 | 284.40 |
| 3 | `c_serial` | 36 | 486.39 |
| 4 | `c_mpi` | 36 | 487.40 |
| 5 | `cpp_mpi` | 36 | 630.38 |
| 6 | `cpp_serial` | 36 | 631.80 |
| 7 | `python_mpi` | 36 | 1581.02 |
| 8 | `python_vectorized` | 36 | 1941.31 |
| 9 | `octave_vectorized` | 36 | 2714.37 |
| 10 | `python_looped` | 20 | 4820.14 |
| 11 | `octave_looped` | 34 | 6611.03 |

These values are specific to the collected termination behaviour, hardware, and software environment. They are not final time-to-convergence rankings.

### Convergence and validation

For the main complete C, C++, OpenMP, and vectorized Python/Octave groups, the current quality split is typically:

```text
14 cases: needs_improvement
22 cases: validated_but_not_converged
0 cases: converged_and_validated
```

The retained cases can show useful Ghia profile agreement while still reaching the maximum iteration count. Profile validation and solver convergence must remain separate.

Representative fields and Ghia plots are available under:

```text
comparison/results/physics_fields/
comparison/figures/physics_final/
```

## 2. Streamfunction–vorticity domain-scaling archive

### Scope

The organized `src/` implementations use a streamfunction–vorticity formulation and repeated fixed-step runs over 18 physical/configuration cases.

Main retained files:

```text
results/final/README_FINAL_STATUS.md
results/final/comparisons/
results/final/cpu_case_summaries/
results/final/figures/
results/audits/
```

### Collected row status

| Family | Successful rows | Failed or time-limited rows | Notes |
|---|---:|---:|---|
| OpenMP | 2,160 | 0 | complete execution archive for the configured C/C++ domain solvers |
| MPI domain | 1,061 | 2,140 | case 13 includes salvaged successful rows |
| Hybrid MPI + threading | 1,044 | 2,100 | case 13 includes salvaged successful rows |

In this archive, `success` means that the process returned successfully and produced a summary row. The solvers use configured step counts, so success is not a universal convergence flag.

### Scaling interpretation

The OpenMP archive is the cleanest execution dataset. Larger cases show useful speedup up to moderate thread counts, followed by lower efficiency at higher counts. Small cases are often dominated by parallel overhead.

The MPI and hybrid archives have high failure or time-limit rates and should not be used as the headline comparison without rerunning a smaller, verified matrix.

Current strong-scaling reports also need to show the pressure solver explicitly. RBGS and RBSOR are distinct configurations and must not appear as duplicate unlabeled rows.

### Exploratory runtime tables

Some retained comparison tables select the minimum runtime across broad backend and case groups. Those tables can collapse language, kernel style, pressure solver, core count, and repetition into one value.

Use them for data exploration only. Paper-quality processing must preserve the full configuration and report repeated-run medians and variability.

## 3. CUDA A100 archive

The current exact RBGS/RBSOR CUDA archive contains 108 rows across 18 cases and two pressure solvers.

All current rows have:

```text
ValidationPass = 0
```

Retained files:

```text
results/cuda/cuda_validation_summary.csv
results/cuda/cuda_cpu_exact_full_summary.csv
results/final/comparisons/cuda_runtime_summary.csv
```

The CUDA timings may be studied as experimental implementation measurements. They must not be presented as validated CPU-versus-GPU speedups.

## What the repository currently supports

- compiled C and C++ implementations are faster than the interpreted loop-based workflows in the original pilot setup;
- the OpenMP domain archive is substantially more complete than the MPI and hybrid archives;
- larger OpenMP cases can benefit from moderate thread counts;
- high thread counts can lose efficiency because of overhead and synchronization;
- RBSOR often executes faster than RBGS in the archived fixed-step runs, subject to numerical-equivalence checks;
- the current CUDA archive requires numerical repair and revalidation.

## What it does not currently support

- one final fastest-language ranking;
- a final time-to-convergence comparison;
- a validated CPU-versus-GPU speedup;
- a fair combined ranking of pressure-correction and streamfunction–vorticity solvers;
- a publishable conclusion based only on minimum observed runtimes.

## Files to inspect first

| File or folder | Purpose |
|---|---|
| `docs/BENCHMARK_TRACKS.md` | boundary between the numerical tracks |
| `comparison/results/final_clean/` | original pressure-correction pilot summaries |
| `comparison/figures/physics_final/` | representative fields and Ghia comparisons |
| `results/final/README_FINAL_STATUS.md` | domain archive execution completeness |
| `results/final/comparisons/cpu_completeness_status.csv` | per-case success and failure counts |
| `results/final/cpu_all_best_by_solver.csv` | detailed fixed-configuration scaling summaries |
| `results/cuda/cuda_validation_summary.csv` | current CUDA Ghia validation status |

## Work remaining before reruns

- normalize domain-solver paths after the `src/` reorganization;
- repair aggregation so pressure solver, kernel, language, and core count remain explicit;
- regenerate corrected tables and figures from existing raw rows;
- separate process completion, convergence, validation, timeout, and runtime-validity fields;
- add schema and path checks to CI;
- clean committed caches, binaries, and backup files.

After those repository tasks, the paper work should return to one converged and validated C++ serial reference case before any large rerun matrix is submitted.
