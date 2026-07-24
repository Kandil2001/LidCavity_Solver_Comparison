# Documentation Index

This work-in-progress repository keeps version-controlled documentation in `docs/` so it functions as a lightweight technical wiki without duplicating content in a separate GitHub Wiki.

## Start here

| Document | Purpose |
|---|---|
| [`PAPER_ROADMAP.md`](PAPER_ROADMAP.md) | Staged plan for turning the project into a reproducible software and benchmark paper |
| [`../benchmark/NUMERICAL_SPECIFICATION.md`](../benchmark/NUMERICAL_SPECIFICATION.md) | Draft frozen numerical method, validation protocol, language scope, and timing rules for the paper |
| [`../benchmark/paper_cases.yaml`](../benchmark/paper_cases.yaml) | Machine-readable draft paper case matrix and convergence targets |
| [`STROMBOLI_NO_GIT.md`](STROMBOLI_NO_GIT.md) | Required snapshot, SCP, extraction, execution, and result-return workflow without using Git on Stromboli |
| [`CURRENT_BENCHMARK_RESULTS.md`](CURRENT_BENCHMARK_RESULTS.md) | Current dataset, interim runtime measurements, convergence interpretation, and remaining work |
| [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md) | Project and numerical-method overview |
| [`IMPLEMENTATION_LAYOUT.md`](IMPLEMENTATION_LAYOUT.md) | Folder layout and implementation structure |
| [`RESULTS_GUIDE.md`](RESULTS_GUIDE.md) | Explanation of result files, CSV outputs, and plots |
| [`RUNNING_ON_HPC.md`](RUNNING_ON_HPC.md) | General notes for Linux and HPC environments |
| [`HOW_TO_PRESENT_THIS_PROJECT.md`](HOW_TO_PRESENT_THIS_PROJECT.md) | Accurate wording for CVs, LinkedIn, interviews, and portfolio use |
| [`COMMUNITY.md`](COMMUNITY.md) | Discussions categories, issue guidance, and community communication |

## Current result folders

| Folder | Purpose |
|---|---|
| `comparison/results/final_clean/` | Current cleaned CSV summaries; the folder name does not indicate project completion |
| `comparison/results/physics_fields/` | Representative physics-field CSVs |
| `comparison/figures/report_pngs/` | Runtime, completeness, residual, and speedup figures |
| `comparison/figures/physics_final/` | Streamlines, vectors, contours, residuals, and Ghia comparison plots |
| `comparison/figures/final_clean/` | Additional cleaned figures retained by the current workflow |

## Project governance files

| File | Purpose |
|---|---|
| [`../LICENSE`](../LICENSE) | MIT license |
| [`../SECURITY.md`](../SECURITY.md) | Security reporting policy |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | Contribution and scientific-honesty guidelines |
| [`../CITATION.cff`](../CITATION.cff) | Citation metadata |
| [`../.github/PULL_REQUEST_TEMPLATE.md`](../.github/PULL_REQUEST_TEMPLATE.md) | Pull-request checklist |
| [`../.github/ISSUE_TEMPLATE/`](../.github/ISSUE_TEMPLATE/) | Issue templates |

## Suggested reading path

1. Read the root `README.md` for project scope and status.
2. Read `PAPER_ROADMAP.md` and the benchmark numerical specification before changing solver behaviour or starting new final runs.
3. Read `STROMBOLI_NO_GIT.md` before transferring or running any paper code on Stromboli.
4. Read `CURRENT_BENCHMARK_RESULTS.md` for the current pilot measurements and limitations.
5. Check `comparison/figures/report_pngs/` for runtime and residual figures.
6. Check `comparison/figures/physics_final/` for streamlines, vectors, contours, and centerline comparisons.
7. Read `HOW_TO_PRESENT_THIS_PROJECT.md` before describing the project in a CV, interview, or public post.

## Why this is not a separate GitHub Wiki

The current documentation is closely tied to code, result files, and project versions. Keeping it in `docs/` means documentation changes can be reviewed and committed with the corresponding implementation changes. A separate GitHub Wiki is not needed at the current project stage.
