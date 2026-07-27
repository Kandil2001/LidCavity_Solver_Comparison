#!/usr/bin/env python3
"""
Create benchmark runtime/accuracy tables and plots for the lid cavity project.

Run after MATLAB, C++, C, and Python benchmarks finish.

    python3 benchmark_report.py \
        --matlab-summary matlab/results/data/study_summary_quick_matlab.csv \
        --cpp-summary cpp/serial/results/data/study_summary_quick.csv \
        --c-summary c/serial/results/data/study_summary_quick.csv \
        --python-summary python/serial/results/data/study_summary_quick.csv \
        --comparison comparison/results/comparison_summary.csv \
        --out comparison/results
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


IMPLEMENTATION_NAME = {
    "vectorized": "MATLAB vectorized",
    "loop": "MATLAB loop",
    "serial_cpp": "C++ serial",
    "serial_c": "C serial baseline",
    "serial_c_looped": "C serial baseline",
    "serial_c_vectorized": "C serial baseline",
    "serial_python": "Python serial vectorized/NumPy",
    "serial_python_vectorized": "Python serial vectorized/NumPy",
    "serial_python_looped": "Python serial looped",
    "python_numpy": "Python serial vectorized/NumPy",
    "openmp_c_looped": "C OpenMP baseline",
    "openmp_c_vectorized_style": "C OpenMP baseline",
    "openmp_c": "C OpenMP baseline",
    "openmp_cpp": "C++ OpenMP",
    "openmp_cpp_looped": "C++ OpenMP",
    "mpi_c_case_parallel_looped": "C MPI case-parallel",
    "mpi_c_case_parallel_vectorized": "C MPI case-parallel",
    "mpi_c_case_parallel": "C MPI case-parallel",
    "mpi_cpp_case_parallel_cpp": "C++ MPI case-parallel",
    "mpi_python_case_parallel_vectorized": "Python MPI case-parallel NumPy",
    "mpi_python_case_parallel_looped": "Python MPI case-parallel looped",
    "cuda_projection_jacobi": "CUDA projection Jacobi",
}


def read_summary(path: Path, source: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing summary file: {path}")
    df = pd.read_csv(path)
    required = {"N", "Re", "Scheme", "PressureSolver", "Implementation", "Runtime_s", "Iterations"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")
    df = df.copy()
    df["Source"] = source
    impl = df["Implementation"].astype(str).str.lower()
    df["ImplementationFull"] = impl.map(IMPLEMENTATION_NAME).fillna(source + " " + df["Implementation"].astype(str))
    df["Scheme"] = df["Scheme"].astype(str).str.lower()
    df["PressureSolver"] = df["PressureSolver"].astype(str).str.upper()
    df["Runtime_s"] = pd.to_numeric(df["Runtime_s"], errors="coerce")
    df["Iterations"] = pd.to_numeric(df["Iterations"], errors="coerce")
    for col in ["FinalRcMass", "FinalRcDiv", "Ghia_u_L2", "Ghia_v_L2", "AvgPoissonIterations"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def case_cols() -> List[str]:
    return ["N", "Re", "Scheme", "PressureSolver"]


def aggregate(df: pd.DataFrame, group_cols: Iterable[str]) -> pd.DataFrame:
    group_cols = list(group_cols)
    named_aggs = {
        "Runs": ("Runtime_s", "count"),
        "TotalRuntime_s": ("Runtime_s", "sum"),
        "MeanRuntime_s": ("Runtime_s", "mean"),
        "MedianRuntime_s": ("Runtime_s", "median"),
        "MinRuntime_s": ("Runtime_s", "min"),
        "MaxRuntime_s": ("Runtime_s", "max"),
        "MeanIterations": ("Iterations", "mean"),
    }
    for col, out in [("FinalRcMass", "MeanFinalRcMass"), ("FinalRcDiv", "MeanFinalRcDiv"), ("Ghia_u_L2", "MeanGhia_u_L2"), ("Ghia_v_L2", "MeanGhia_v_L2")]:
        if col in df.columns:
            named_aggs[out] = (col, "mean")
    return df.groupby(group_cols, dropna=False).agg(**named_aggs).reset_index()


def make_runtime_pivot(df: pd.DataFrame) -> pd.DataFrame:
    pivot = df.pivot_table(
        index=case_cols(),
        columns="ImplementationFull",
        values="Runtime_s",
        aggfunc="first",
    ).reset_index()
    pivot.columns.name = None

    baseline_names = [c for c in ["C++ serial", "C serial baseline", "Python serial vectorized/NumPy", "Python serial looped", "MATLAB vectorized", "MATLAB loop"] if c in pivot.columns]
    for baseline in baseline_names:
        safe_base = baseline.replace(" ", "_").replace("/", "_").replace("+", "p")
        for col in [c for c in pivot.columns if c not in case_cols() and not c.startswith("Ratio_")]:
            if col == baseline:
                continue
            safe_col = col.replace(" ", "_").replace("/", "_").replace("+", "p")
            pivot[f"Ratio_{safe_col}_over_{safe_base}"] = pivot[col] / pivot[baseline]
    return pivot


def fastest_by_case(df: pd.DataFrame) -> pd.DataFrame:
    idx = df.groupby(case_cols())["Runtime_s"].idxmin()
    cols = case_cols() + ["ImplementationFull", "Runtime_s", "Iterations", "Status", "Quality"]
    cols = [c for c in cols if c in df.columns]
    return df.loc[idx, cols].sort_values(case_cols()).reset_index(drop=True)


def bar_plot(df: pd.DataFrame, x_col: str, y_col: str, title: str, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df[x_col].astype(str), df[y_col])
    ax.set_title(title)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def grouped_line_plot(df: pd.DataFrame, x_col: str, y_col: str, title: str, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    for impl, sub in df.groupby("ImplementationFull"):
        sub = sub.sort_values(x_col)
        ax.plot(sub[x_col], sub[y_col], marker="o", label=impl)
    ax.set_title(title)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def ratio_plot(pivot: pd.DataFrame, out: Path, baseline_hint: str = "C++ serial") -> None:
    if baseline_hint in pivot.columns:
        suffix = "over_" + baseline_hint.replace(" ", "_").replace("/", "_").replace("+", "p")
        cols = [c for c in pivot.columns if c.startswith("Ratio_") and c.endswith(suffix)]
    else:
        cols = [c for c in pivot.columns if c.startswith("Ratio_")]
    if not cols:
        return
    labels = []
    values = []
    for col in cols:
        labels.append(col.replace("Ratio_", "").replace("_over_", " / ").replace("_", " "))
        values.append(float(pivot[col].dropna().mean()))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(labels, values)
    ax.set_title(f"Mean runtime ratios")
    ax.set_ylabel("Runtime ratio")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def fmt_seconds(x: float) -> str:
    if not math.isfinite(x):
        return "n/a"
    if x < 60:
        return f"{x:.2f} s"
    if x < 3600:
        return f"{x/60:.2f} min"
    return f"{x/3600:.2f} h"


def write_markdown_report(
    out_path: Path,
    all_runs: pd.DataFrame,
    impl_agg: pd.DataFrame,
    pivot: pd.DataFrame,
    fastest: pd.DataFrame,
    comparison: pd.DataFrame | None,
    loaded_sources: List[Tuple[str, Path]],
) -> None:
    lines: List[str] = []
    lines.append("# Full Serial Lid-Cavity Benchmark Report\n\n")
    lines.append("## What was run\n\n")
    lines.append("Shared benchmark grid, depending on selected mode:\n\n")
    lines.append("- Mesh sizes: `N = 32, 64, 128` for full mode\n")
    lines.append("- Reynolds numbers: `Re = 100, 400, 1000` for full mode\n")
    lines.append("- Numerical schemes: `upwind`, `central`\n")
    lines.append("- Pressure solvers: `RBGS`, `RBSOR`\n")
    lines.append("- Implementations included in loaded summaries: " + ", ".join(f"`{x}`" for x in sorted(all_runs["ImplementationFull"].unique())) + "\n\n")
    lines.append("Loaded summary files:\n")
    for label, path in loaded_sources:
        lines.append(f"- **{label}**: `{path}`\n")
    lines.append(f"\nTotal completed runs in summaries: **{len(all_runs)}**. For a full all-serial package run, expected total is **252**: 72 MATLAB cases, 36 C++ cases, 72 C cases, and 72 Python cases.\n\n")

    lines.append("## Runtime summary by implementation\n\n")
    impl_show = impl_agg[["ImplementationFull", "Runs", "TotalRuntime_s", "MeanRuntime_s", "MedianRuntime_s", "MinRuntime_s", "MaxRuntime_s", "MeanIterations"]].copy()
    impl_show["TotalRuntime"] = impl_show["TotalRuntime_s"].map(fmt_seconds)
    impl_show["MeanRuntime"] = impl_show["MeanRuntime_s"].map(fmt_seconds)
    impl_show["MedianRuntime"] = impl_show["MedianRuntime_s"].map(fmt_seconds)
    impl_show = impl_show[["ImplementationFull", "Runs", "TotalRuntime", "MeanRuntime", "MedianRuntime", "MinRuntime_s", "MaxRuntime_s", "MeanIterations"]]
    lines.append(impl_show.to_markdown(index=False))
    lines.append("\n\n")

    ratio_cols = [c for c in pivot.columns if c.startswith("Ratio_")]
    if ratio_cols:
        lines.append("## Mean runtime ratios\n\n")
        for col in ratio_cols:
            lines.append(f"- `{col}` mean: `{pivot[col].mean(skipna=True):.3f}`\n")
        lines.append("\nA value larger than 1 means the numerator implementation was slower than the denominator implementation for that case.\n\n")

    lines.append("## Fastest implementation by case\n\n")
    count_fast = fastest["ImplementationFull"].value_counts().rename_axis("ImplementationFull").reset_index(name="FastestCaseCount")
    lines.append(count_fast.to_markdown(index=False))
    lines.append("\n\n")

    if comparison is not None and not comparison.empty:
        lines.append("## Field-difference summary against reference\n\n")
        for col in ["u_Linf", "v_Linf", "speed_Linf", "p_centered_Linf", "u_centerline_L2", "v_centerline_L2", "Ghia_u_L2_abs_diff", "Ghia_v_L2_abs_diff"]:
            if col in comparison.columns:
                lines.append(f"- Worst `{col}`: `{comparison[col].max(skipna=True):.6e}`\n")
        lines.append("\n")

    lines.append("## Files generated\n\n")
    lines.append("- `all_runs_long.csv`: one row per run across all loaded implementations.\n")
    lines.append("- `runtime_pivot_by_case.csv`: one row per setup, with runtimes side-by-side.\n")
    lines.append("- `comparison_summary.csv`: field and validation differences against the selected reference.\n")
    lines.append("- `aggregate_by_*.csv`: grouped runtime and accuracy summaries.\n")
    lines.append("- `*.png`: runtime plots for README, GitHub, and LinkedIn.\n\n")
    lines.append("## Interpretation note\n\n")
    lines.append("Use the internal `Runtime_s` column for solver-speed comparison. It measures the solver case itself, not the time spent writing CSV files or creating figures. For a clean ladder, read the results as: MATLAB vectorized/looped, Python vectorized/looped, C++ serial, C serial baseline, then later OpenMP/MPI/CUDA extensions.\n")

    out_path.write_text("".join(lines), encoding="utf-8")


def parse_summary_arg(values: Optional[List[str]]) -> List[Tuple[str, Path]]:
    out: List[Tuple[str, Path]] = []
    if not values:
        return out
    for item in values:
        if "=" not in item:
            raise ValueError(f"--summary expects LABEL=PATH, got: {item}")
        label, path = item.split("=", 1)
        out.append((label.strip(), Path(path.strip())))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Create runtime and benchmark summaries.")
    parser.add_argument("--summary", action="append", default=None, help="Additional summary as LABEL=PATH")
    parser.add_argument("--matlab-summary", type=Path, default=None)
    parser.add_argument("--cpp-summary", type=Path, default=None)
    parser.add_argument("--c-summary", type=Path, default=None)
    parser.add_argument("--python-summary", type=Path, default=None)
    parser.add_argument("--comparison", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=Path("comparison/results"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    sources: List[Tuple[str, Path]] = []
    if args.matlab_summary is not None:
        sources.append(("MATLAB", args.matlab_summary))
    if args.cpp_summary is not None:
        sources.append(("C++", args.cpp_summary))
    if args.c_summary is not None:
        sources.append(("C", args.c_summary))
    if args.python_summary is not None:
        sources.append(("Python", args.python_summary))
    sources.extend(parse_summary_arg(args.summary))
    if not sources:
        raise ValueError("No summary files supplied. Use --matlab-summary, --cpp-summary, --c-summary, --python-summary, or --summary LABEL=PATH.")

    frames = [read_summary(path, label) for label, path in sources]
    all_runs = pd.concat(frames, ignore_index=True)
    all_runs = all_runs.sort_values(["N", "Re", "Scheme", "PressureSolver", "ImplementationFull"]).reset_index(drop=True)

    all_runs.to_csv(args.out / "all_runs_long.csv", index=False)

    pivot = make_runtime_pivot(all_runs)
    pivot.to_csv(args.out / "runtime_pivot_by_case.csv", index=False)

    impl_agg = aggregate(all_runs, ["ImplementationFull"])
    impl_agg.to_csv(args.out / "aggregate_by_implementation.csv", index=False)
    aggregate(all_runs, ["ImplementationFull", "N"]).to_csv(args.out / "aggregate_by_mesh.csv", index=False)
    aggregate(all_runs, ["ImplementationFull", "Re"]).to_csv(args.out / "aggregate_by_re.csv", index=False)
    aggregate(all_runs, ["ImplementationFull", "Scheme"]).to_csv(args.out / "aggregate_by_scheme.csv", index=False)
    aggregate(all_runs, ["ImplementationFull", "PressureSolver"]).to_csv(args.out / "aggregate_by_pressure_solver.csv", index=False)

    fastest = fastest_by_case(all_runs)
    fastest.to_csv(args.out / "fastest_by_case.csv", index=False)

    bar_plot(impl_agg, "ImplementationFull", "MeanRuntime_s", "Mean runtime by implementation", args.out / "runtime_by_implementation.png")
    mesh_agg = aggregate(all_runs, ["ImplementationFull", "N"])
    grouped_line_plot(mesh_agg, "N", "MeanRuntime_s", "Mean runtime vs mesh size", args.out / "runtime_by_mesh.png")
    re_agg = aggregate(all_runs, ["ImplementationFull", "Re"])
    grouped_line_plot(re_agg, "Re", "MeanRuntime_s", "Mean runtime vs Reynolds number", args.out / "runtime_by_re.png")
    ratio_plot(pivot, args.out / "runtime_ratios.png")
    # Backward-compatible filename used by the original package.
    ratio_plot(pivot, args.out / "speedup_matlab_over_cpp.png", baseline_hint="C++ serial")

    comparison = None
    if args.comparison and args.comparison.exists():
        comparison = pd.read_csv(args.comparison)

    write_markdown_report(args.out / "benchmark_report.md", all_runs, impl_agg, pivot, fastest, comparison, sources)

    print(f"Wrote benchmark outputs to: {args.out}")
    print(f"Total runs loaded: {len(all_runs)}")
    print("Main files:")
    print(f"  {args.out / 'benchmark_report.md'}")
    print(f"  {args.out / 'runtime_pivot_by_case.csv'}")
    print(f"  {args.out / 'all_runs_long.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
