#!/usr/bin/env python3
"""Build the small, README-facing result set from the archived domain runs.

This script does not run CFD. It reads the existing repeated fixed-workload
summaries, selects one representative largest-grid case, and writes compact CSV,
Markdown, and SVG outputs under ``results/selected``.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "results" / "final"
OUT = ROOT / "results" / "selected"
FIGURES = OUT / "figures"

CASE_INDEX = 16
CASE_NAME = "N128_Re400_central_RBSOR"
FAMILIES = ("openmp", "mpi", "hybrid")


def read_case(family: str) -> pd.DataFrame:
    path = FINAL / "cpu_case_summaries" / f"{family}_case_{CASE_INDEX}" / "strong_scaling_summary.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Missing archived summary: {path}")
    data = pd.read_csv(path)
    required = {
        "solver_group", "language", "parallel_model", "kernel_style", "N", "Re",
        "scheme", "pressure", "steps", "poisson_iters", "total_cores", "mpi_ranks",
        "threads_per_rank", "runs", "runtime_median_s", "speedup_vs_baseline",
        "parallel_efficiency",
    }
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(f"{path} is missing columns: {', '.join(missing)}")
    data.insert(0, "family", family)
    return data


def select_case() -> pd.DataFrame:
    frames = [read_case(family) for family in FAMILIES]
    data = pd.concat(frames, ignore_index=True)
    selected = data[
        (data["N"] == 128)
        & (data["Re"] == 400)
        & (data["scheme"].astype(str).str.lower() == "central")
        & (data["pressure"].astype(str).str.upper() == "RBSOR")
    ].copy()
    if selected.empty:
        raise RuntimeError("Representative N=128, Re=400, central, RBSOR rows were not found.")
    return selected.sort_values(["family", "solver_group", "total_cores"]).reset_index(drop=True)


def write_completeness() -> pd.DataFrame:
    path = FINAL / "comparisons" / "cpu_completeness_status.csv"
    data = pd.read_csv(path)
    summary = (
        data.groupby("family", as_index=False)
        .agg(
            configured_rows=("raw_rows", "sum"),
            successful_rows=("success_rows", "sum"),
            failed_or_timed_out_rows=("failed_rows", "sum"),
            complete_cases=("success_rows", lambda values: int((values == 120).sum())),
        )
    )
    summary["success_rate"] = summary["successful_rows"] / summary["configured_rows"]
    summary.to_csv(OUT / "execution_completeness.csv", index=False)
    return summary


def write_highlights(selected: pd.DataFrame) -> pd.DataFrame:
    vectorized = selected[selected["kernel_style"] == "vectorized"].copy()
    highlights = (
        vectorized.sort_values("runtime_median_s")
        .groupby("solver_group", as_index=False)
        .first()
    )
    columns = [
        "family", "solver_group", "language", "parallel_model", "kernel_style", "N", "Re",
        "scheme", "pressure", "steps", "poisson_iters", "total_cores", "mpi_ranks",
        "threads_per_rank", "runs", "runtime_median_s", "speedup_vs_baseline",
        "parallel_efficiency",
    ]
    highlights = highlights[columns].sort_values(["family", "language", "solver_group"])
    highlights.to_csv(OUT / "highlights.csv", index=False)
    return highlights


def fmt(value: float, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def write_readme(highlights: pd.DataFrame, completeness: pd.DataFrame) -> None:
    by_solver = highlights.set_index("solver_group")
    c = by_solver.loc["c_openmp_domain_vectorized"]
    cpp = by_solver.loc["cpp_openmp_domain_vectorized"]
    mpi = by_solver.loc["python_mpi_domain_vectorized"]
    hybrid = by_solver.loc["python_hybrid_mpi_threaded_vectorized"]

    lines = [
        "# Selected archived results",
        "",
        "This directory contains the small result set used by the root README.",
        "It is generated from the existing repeated **grid/domain-decomposition** archive by:",
        "",
        "```bash",
        "python3 scripts/generate_selected_results.py",
        "```",
        "",
        "No CFD case is executed by that command.",
        "",
        "## Representative fixed workload",
        "",
        "- Grid: `N = 128`",
        "- Reynolds number: `Re = 400`",
        "- Convection scheme: `central`",
        "- Poisson method: `RBSOR`",
        "- Outer steps: `2500`",
        "- Poisson iterations per step: `250`",
        "- Repetitions per configuration: `3`",
        "",
        "| Implementation | Best archived configuration | Median runtime [s] | Speedup | Efficiency |",
        "|---|---:|---:|---:|---:|",
        f"| C OpenMP vectorized | {int(c.total_cores)} threads | {fmt(c.runtime_median_s)} | {fmt(c.speedup_vs_baseline)}× | {fmt(100*c.parallel_efficiency, 1)}% |",
        f"| C++ OpenMP vectorized | {int(cpp.total_cores)} threads | {fmt(cpp.runtime_median_s)} | {fmt(cpp.speedup_vs_baseline)}× | {fmt(100*cpp.parallel_efficiency, 1)}% |",
        f"| Python pure-MPI vectorized | {int(mpi.mpi_ranks)} ranks | {fmt(mpi.runtime_median_s)} | {fmt(mpi.speedup_vs_baseline)}× | {fmt(100*mpi.parallel_efficiency, 1)}% |",
        f"| Python hybrid vectorized | {int(hybrid.mpi_ranks)} ranks × {int(hybrid.threads_per_rank)} threads | {fmt(hybrid.runtime_median_s)} | {fmt(hybrid.speedup_vs_baseline)}× | {fmt(100*hybrid.parallel_efficiency, 1)}% |",
        "",
        "The C and C++ MPI/hybrid archive rows are not included because those historical jobs did not rebuild successfully. The Makefiles are repaired in the repository, but those configurations require rerunning before a cross-language distributed-memory comparison can be made.",
        "",
        "## Interpretation",
        "",
        "- C and C++ OpenMP performance is nearly identical for the selected vectorized workload.",
        "- Four OpenMP threads are the useful point in this archived case; runtime increases beyond that.",
        "- Python pure MPI scales better than the Python hybrid layout for this workload.",
        "- These are fixed-step performance measurements, not convergence-controlled time-to-solution results.",
        "",
        "## Files",
        "",
        "- `scaling_case_n128_re400_central_rbsor.csv`: every retained scaling point for the selected case.",
        "- `highlights.csv`: best vectorized point per solver.",
        "- `execution_completeness.csv`: execution success/failure totals for the archived grid-decomposition study.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    selected = select_case()
    selected.to_csv(OUT / "scaling_case_n128_re400_central_rbsor.csv", index=False)
    completeness = write_completeness()
    highlights = write_highlights(selected)
    write_readme(highlights, completeness)
    print(f"Wrote selected results to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
