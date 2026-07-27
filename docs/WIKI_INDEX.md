# Documentation Index

This work-in-progress repository keeps version-controlled documentation in `docs/` so it functions as a lightweight technical wiki without duplicating content in a separate GitHub Wiki.

## Start here

| Document | Purpose |
|---|---|
| [`CURRENT_BENCHMARK_RESULTS.md`](CURRENT_BENCHMARK_RESULTS.md) | Current dataset, interim runtime measurements, convergence interpretation, and remaining work |
| [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md) | Project and numerical-method overview |
| [`IMPLEMENTATION_LAYOUT.md`](IMPLEMENTATION_LAYOUT.md) | Folder layout and implementation structure |
| [`RESULTS_GUIDE.md`](RESULTS_GUIDE.md) | Explanation of result files, CSV outputs, and plots |
| [`RUNNING_ON_HPC.md`](RUNNING_ON_HPC.md) | Notes for Linux and HPC environments |
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
2. Read `CURRENT_BENCHMARK_RESULTS.md` for the current measurements and limitations.
3. Check `comparison/figures/report_pngs/` for runtime and residual figures.
4. Check `comparison/figures/physics_final/` for streamlines, vectors, contours, and centerline comparisons.
5. Read `HOW_TO_PRESENT_THIS_PROJECT.md` before describing the project in a CV, interview, or public post.

## Why this is not a separate GitHub Wiki

The current documentation is closely tied to code, result files, and project versions. Keeping it in `docs/` means documentation changes can be reviewed and committed with the corresponding implementation changes. A separate GitHub Wiki is not needed at the current project stage.
