# Results guide

This repository retains results from two numerical tracks. Always identify the track before comparing files.

See [`BENCHMARK_TRACKS.md`](BENCHMARK_TRACKS.md) for the numerical boundary between the pressure-correction and streamfunction–vorticity datasets.

## Track A — pressure-correction pilot results

Implementation-local outputs are written under each original top-level solver folder:

```text
results/data/      summaries, fields, residual histories, validation data
results/figures/   field, residual, and validation plots
results/scaling/   implementation-specific scaling tables
results/logs/      optional run logs
```

Repository-level retained pilot outputs are under:

```text
comparison/results/final_clean/
comparison/results/physics_fields/
comparison/figures/report_pngs/
comparison/figures/physics_final/
```

### Original serial comparison

From the repository root:

```bash
make compare-serial MODE=quick
make report-serial MODE=quick
```

Cases are matched by:

```text
mesh size, Reynolds number, convection scheme, pressure solver
```

The current pilot tables separate implementations by language and execution mode, but many cases reached their iteration limit. Treat their runtimes as execution-time measurements, not final time-to-convergence results.

## Track B — fixed-step domain-scaling archive

The organized streamfunction–vorticity source tree writes local outputs below `src/.../results/`. Selected repeated data is retained under:

```text
results/final/cpu_case_summaries/
results/final/comparisons/
results/final/figures/
results/audits/
```

The current archived families are:

```text
OpenMP domain
MPI domain decomposition
hybrid MPI + threading
```

The runs use configured step counts. In the raw scaling files, `status=success` means that the program completed and produced a summary row. It does not establish one common convergence decision.

## CUDA archive

CUDA summaries and Ghia validation tables are stored under:

```text
results/cuda/
results/final/comparisons/
```

The current A100 RBGS/RBSOR validation rows do not pass the configured Ghia thresholds. Keep CUDA runtime and validation reporting separate.

## Status terminology

Use separate fields and wording for:

```text
ExecutionCompleted
OuterConverged
PressureConverged
ValidationPassed
TimedOut
RuntimeValid
```

When an archived file does not contain enough information to reconstruct a numerical status, record `unknown`; do not infer convergence from process completion.

## Performance aggregation rules

Paper-quality performance tables should preserve:

```text
NumericalTrack
Language
Implementation
ParallelModel
KernelStyle
PressureSolver
N
Re
Scheme
TotalCores
MPIRanks
ThreadsPerRank
Repeat
```

For each fixed configuration, report at least:

```text
run count
minimum
median
mean
standard deviation
interquartile range
maximum
```

Use the median and variability for conclusions. A table that selects only the minimum runtime across language, kernel, pressure solver, or core count is exploratory and must not be presented as a fair ranking.

## Strong-scaling reports

Strong-scaling tables and plots must include the pressure solver in their grouping and labels. RBGS and RBSOR rows must not appear as duplicate unlabeled entries or be connected as one curve.

Speedup must use the smallest available core count for the same:

```text
case
solver implementation
kernel style
pressure solver
```

## Automated studies in the original track

Grid trend:

```bash
make grid-convergence
```

Validation plots:

```bash
make validation-plots
python3 scripts/plot_validation_centerlines.py --Re 100 --N 64
```

These are useful development checks, but Ghia comparison is validation rather than formal code verification. Manufactured or analytical operator tests are still required for a publishable verification claim.

## Git policy

Generated outputs are ignored by default. Retain only selected raw evidence, summaries, and figures that are documented and needed to reproduce a reported conclusion. Do not commit caches, binaries, or temporary backup scripts.
