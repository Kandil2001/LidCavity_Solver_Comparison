# Documentation index

This repository keeps version-controlled documentation in `docs/` so numerical-method changes, result interpretation, and code changes can be reviewed together.

## Start here

| Document | Purpose |
|---|---|
| [`BENCHMARK_TRACKS.md`](BENCHMARK_TRACKS.md) | Canonical separation between the pressure-correction and streamfunction–vorticity tracks |
| [`CURRENT_BENCHMARK_RESULTS.md`](CURRENT_BENCHMARK_RESULTS.md) | Current evidence, execution counts, limitations, and remaining cleanup work |
| [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md) | Physical problem, numerical formulations, and publication direction |
| [`IMPLEMENTATION_LAYOUT.md`](IMPLEMENTATION_LAYOUT.md) | Canonical source paths and implementation structure |
| [`RESULTS_GUIDE.md`](RESULTS_GUIDE.md) | Result locations, status terminology, aggregation rules, and plot interpretation |
| [`RUNNING_ON_HPC.md`](RUNNING_ON_HPC.md) | Linux and HPC notes |
| [`HOW_TO_PRESENT_THIS_PROJECT.md`](HOW_TO_PRESENT_THIS_PROJECT.md) | Accurate wording for CVs, LinkedIn, interviews, and portfolio use |
| [`COMMUNITY.md`](COMMUNITY.md) | Discussions categories, issue guidance, and community communication |

## Pressure-correction pilot results

| Folder | Purpose |
|---|---|
| `comparison/results/final_clean/` | Cleaned execution, runtime, residual, and quality summaries |
| `comparison/results/physics_fields/` | Representative field CSVs |
| `comparison/figures/report_pngs/` | Runtime, completeness, residual, and speedup figures |
| `comparison/figures/physics_final/` | Streamlines, contours, vectors, residuals, and Ghia plots |
| `comparison/figures/final_clean/` | Additional retained pilot figures |

## Domain-scaling and CUDA archives

| Folder | Purpose |
|---|---|
| `results/final/cpu_case_summaries/` | Per-case strong-scaling rows and reports |
| `results/final/comparisons/` | Aggregated execution and exploratory runtime tables |
| `results/final/figures/` | Retained scaling and backend figures |
| `results/cuda/` | CUDA runtime summaries and Ghia validation status |
| `results/audits/` | Repository and result audits |
| `data/cases/` | Domain-scaling case definitions |
| `hpc/stromboli/` | Slurm scripts for the organized scaling track |

## Suggested reading path

1. Read the root `README.md` for the current scientific status.
2. Read `BENCHMARK_TRACKS.md` before comparing any result folders.
3. Read `CURRENT_BENCHMARK_RESULTS.md` for the evidence currently retained.
4. Use `RESULTS_GUIDE.md` before regenerating tables or figures.
5. Use `IMPLEMENTATION_LAYOUT.md` before modifying run-script paths.
6. Read `HOW_TO_PRESENT_THIS_PROJECT.md` before making public claims.

## Project governance

| File | Purpose |
|---|---|
| [`../LICENSE`](../LICENSE) | MIT license |
| [`../SECURITY.md`](../SECURITY.md) | Security reporting policy |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | Contribution and scientific-honesty guidance |
| [`../CITATION.cff`](../CITATION.cff) | Citation metadata |
| [`../.github/PULL_REQUEST_TEMPLATE.md`](../.github/PULL_REQUEST_TEMPLATE.md) | Pull-request checklist |
| [`../.github/ISSUE_TEMPLATE/`](../.github/ISSUE_TEMPLATE/) | Issue templates |

## Why this is not a separate GitHub Wiki

The documentation is tightly connected to source code, raw result schemas, and versioned interpretation. Keeping it in `docs/` allows every change to be reviewed with the implementation or data-processing change that motivated it.
