#!/usr/bin/env python3
"""Aggregate full-study CSV data without creating figures.

This is the data-first postprocessing step for the Stromboli run. It collects
summary CSV files from all implementations, computes meaningful comparison
tables, extracts residual-history statistics, and calculates grid-convergence
orders from already-computed full-study grids.

No PNG/PDF/SVG files are created by this script.
"""
from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SourceDef:
    label: str
    family: str
    method: str
    path: Path
    threads: Optional[int] = None
    ranks: Optional[int] = None


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def safe_read_csv(path: Path) -> Optional[pd.DataFrame]:
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        print(f"Skipping unreadable CSV {path}: {exc}")
        return None
    if df.empty:
        return None
    return df


def known_sources(root: Path, mode: str) -> List[SourceDef]:
    raw = root / "comparison" / "results" / "raw"
    sources = [
        SourceDef("MATLAB/Octave serial", "MATLAB/Octave", "serial", root / "matlab" / "results" / "data" / f"study_summary_{mode}_matlab.csv"),
        SourceDef("Python serial", "Python", "serial", root / "python" / "serial" / "results" / "data" / f"study_summary_{mode}.csv"),
        SourceDef("C serial", "C", "serial", root / "c" / "serial" / "results" / "data" / f"study_summary_{mode}.csv"),
        SourceDef("C++ serial", "C++", "serial", root / "cpp" / "serial" / "results" / "data" / f"study_summary_{mode}.csv"),
        SourceDef("C OpenMP latest", "C", "OpenMP", root / "c" / "openmp" / "results" / "data" / f"study_summary_{mode}.csv"),
        SourceDef("C++ OpenMP latest", "C++", "OpenMP", root / "cpp" / "openmp" / "results" / "data" / f"study_summary_{mode}.csv"),
        SourceDef("C MPI latest", "C", "MPI case-parallel", root / "c" / "mpi" / "results" / "data" / "study_summary_mpi.csv"),
        SourceDef("C++ MPI latest", "C++", "MPI case-parallel", root / "cpp" / "mpi" / "results" / "data" / "study_summary_mpi.csv"),
        SourceDef("Python MPI latest", "Python", "MPI case-parallel", root / "python" / "mpi" / "results" / "data" / "study_summary_mpi.csv"),
    ]
    # Raw copies made by the Slurm submit script preserve each thread/rank run.
    if raw.exists():
        for p in sorted(raw.glob("*.csv")):
            name = p.stem.lower()
            family = "Unknown"
            method = "unknown"
            threads = None
            ranks = None
            if "matlab" in name or "octave" in name:
                family, method = "MATLAB/Octave", "serial"
            elif "python" in name:
                family = "Python"
            elif "cpp" in name:
                family = "C++"
            elif re.search(r"(^|_)c(_|$)", name):
                family = "C"
            if "openmp" in name:
                method = "OpenMP"
            elif "mpi" in name:
                method = "MPI case-parallel"
            elif method == "unknown":
                method = "serial"
            mt = re.search(r"(?:threads?|t)(\d+)", name)
            mr = re.search(r"(?:ranks?|r)(\d+)", name)
            if mt:
                threads = int(mt.group(1))
            if mr:
                ranks = int(mr.group(1))
            label = p.stem.replace("_", " ")
            sources.append(SourceDef(label, family, method, p, threads, ranks))
    return sources


def normalize_summary(df: pd.DataFrame, src: SourceDef, root: Path) -> pd.DataFrame:
    out = df.copy()
    out.insert(0, "SourceLabel", src.label)
    out.insert(1, "SolverFamily", src.family)
    out.insert(2, "ParallelMethod", src.method)
    out.insert(3, "Threads", src.threads if src.threads is not None else np.nan)
    out.insert(4, "Ranks", src.ranks if src.ranks is not None else np.nan)
    out.insert(5, "SummaryPath", str(src.path.relative_to(root)) if src.path.is_relative_to(root) else str(src.path))
    # Consistent types/casing
    for col in ["N", "Re", "Runtime_s", "Iterations", "LocalMaxIter", "FinalRu", "FinalRv", "FinalRcMass", "FinalRcDiv", "AvgPoissonIterations", "AvgPoissonRelResidual", "PressureSaturationRatio", "Ghia_u_L2", "Ghia_v_L2", "Ghia_u_Linf", "Ghia_v_Linf"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in ["Scheme", "PressureSolver", "Implementation", "Status", "Quality"]:
        if col in out.columns:
            out[col] = out[col].astype(str)
    if "Ghia_u_L2" in out.columns and "Ghia_v_L2" in out.columns:
        out["Ghia_combined_L2"] = np.sqrt(out["Ghia_u_L2"] ** 2 + out["Ghia_v_L2"] ** 2)
    else:
        out["Ghia_combined_L2"] = np.nan
    out["CaseKey"] = (
        "N" + out.get("N", pd.Series(np.nan, index=out.index)).astype("Int64").astype(str)
        + "_Re" + out.get("Re", pd.Series(np.nan, index=out.index)).astype("Int64").astype(str)
        + "_" + out.get("Scheme", pd.Series("", index=out.index)).astype(str).str.lower()
        + "_" + out.get("PressureSolver", pd.Series("", index=out.index)).astype(str).str.upper()
    )
    return out


def load_all_summaries(root: Path, mode: str) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    seen: set[Path] = set()
    for src in known_sources(root, mode):
        if src.path in seen:
            continue
        seen.add(src.path)
        df = safe_read_csv(src.path)
        if df is None:
            continue
        frames.append(normalize_summary(df, src, root))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True, sort=False)


def finite_positive(x: object) -> bool:
    try:
        v = float(x)
    except Exception:
        return False
    return math.isfinite(v) and v > 0


def compute_grid_convergence(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    needed = {"SolverFamily", "ParallelMethod", "Implementation", "Re", "Scheme", "PressureSolver", "N", "Ghia_u_L2", "Ghia_v_L2", "Ghia_combined_L2"}
    if not needed.issubset(df.columns):
        return pd.DataFrame()

    rows: List[Dict[str, object]] = []
    group_cols = ["SourceLabel", "SolverFamily", "ParallelMethod", "Implementation", "Threads", "Ranks", "Re", "Scheme", "PressureSolver"]
    # Use dropna=False so serial rows with blank thread/rank are kept.
    for keys, sub in df.dropna(subset=["N"]).groupby(group_cols, dropna=False):
        sub = sub.sort_values("N").drop_duplicates(subset=["N"], keep="last")
        if len(sub) < 2:
            continue
        ns = sub["N"].astype(int).tolist()
        if not set([32, 64, 128]).issubset(set(ns)):
            enough_three = False
        else:
            enough_three = True
        for i in range(1, len(sub)):
            c = sub.iloc[i - 1]
            f = sub.iloc[i]
            h_c = 1.0 / (float(c["N"]) - 1.0)
            h_f = 1.0 / (float(f["N"]) - 1.0)
            row: Dict[str, object] = dict(zip(group_cols, keys))
            row.update({
                "N_coarse": int(c["N"]),
                "N_fine": int(f["N"]),
                "Has_32_64_128": int(enough_three),
            })
            for err_col, name in [("Ghia_u_L2", "u"), ("Ghia_v_L2", "v"), ("Ghia_combined_L2", "combined")]:
                e_c = c.get(err_col, np.nan)
                e_f = f.get(err_col, np.nan)
                row[f"Error_{name}_coarse"] = e_c
                row[f"Error_{name}_fine"] = e_f
                if finite_positive(e_c) and finite_positive(e_f) and h_c != h_f:
                    row[f"ObservedOrder_{name}"] = math.log(float(e_c) / float(e_f)) / math.log(h_c / h_f)
                else:
                    row[f"ObservedOrder_{name}"] = np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def comparison_tables(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    tables: Dict[str, pd.DataFrame] = {}
    if df.empty:
        return tables
    numeric = ["Runtime_s", "Iterations", "FinalRcMass", "FinalRcDiv", "Ghia_u_L2", "Ghia_v_L2", "Ghia_combined_L2", "AvgPoissonIterations", "AvgPoissonRelResidual", "PressureSaturationRatio"]
    for col in numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    tables["case_counts"] = df.groupby(["SourceLabel", "SolverFamily", "ParallelMethod"], dropna=False).agg(
        cases=("CaseID", "count"),
        ok_cases=("Status", lambda s: int((s.astype(str).str.lower() == "converged").sum())),
        validation_passes=("ValidationPass", lambda s: int(pd.to_numeric(s, errors="coerce").fillna(0).sum()) if "ValidationPass" in df.columns else 0),
        runtime_total_s=("Runtime_s", "sum"),
        runtime_median_s=("Runtime_s", "median"),
        ghia_combined_median=("Ghia_combined_L2", "median"),
        mass_residual_median=("FinalRcMass", "median"),
    ).reset_index()

    keys = ["N", "Re", "Scheme", "PressureSolver"]
    base_mask = (df["SolverFamily"].eq("C++") & df["ParallelMethod"].eq("serial"))
    base = df.loc[base_mask, keys + ["Runtime_s", "Ghia_combined_L2"]].rename(columns={
        "Runtime_s": "CPP_serial_Runtime_s",
        "Ghia_combined_L2": "CPP_serial_Ghia_combined_L2",
    })
    if not base.empty:
        base = base.drop_duplicates(subset=keys, keep="last")
        rel = df.merge(base, on=keys, how="left")
        rel["Runtime_relative_to_CPP_serial"] = rel["Runtime_s"] / rel["CPP_serial_Runtime_s"]
        rel["Accuracy_ratio_to_CPP_serial"] = rel["Ghia_combined_L2"] / rel["CPP_serial_Ghia_combined_L2"]
        tables["casewise_relative_to_cpp_serial"] = rel

    best_cols = keys + ["SourceLabel", "SolverFamily", "ParallelMethod", "Implementation", "Threads", "Ranks", "Runtime_s", "Ghia_combined_L2", "FinalRcMass", "Quality"]
    existing_best_cols = [c for c in best_cols if c in df.columns]
    if all(c in df.columns for c in keys + ["Runtime_s"]):
        best_runtime = df.dropna(subset=["Runtime_s"]).sort_values("Runtime_s").groupby(keys, dropna=False).head(3)[existing_best_cols]
        tables["top3_fastest_per_case"] = best_runtime
    if all(c in df.columns for c in keys + ["Ghia_combined_L2"]):
        best_error = df.dropna(subset=["Ghia_combined_L2"]).sort_values("Ghia_combined_L2").groupby(keys, dropna=False).head(3)[existing_best_cols]
        tables["top3_lowest_error_per_case"] = best_error

    # Compare schemes and pressure solvers at the same N/Re/solver.
    agg_cols = ["SourceLabel", "SolverFamily", "ParallelMethod", "N", "Re", "Scheme", "PressureSolver"]
    tables["scheme_pressure_summary"] = df.groupby(agg_cols, dropna=False).agg(
        cases=("CaseID", "count"),
        median_runtime_s=("Runtime_s", "median"),
        median_combined_L2=("Ghia_combined_L2", "median"),
        median_mass_residual=("FinalRcMass", "median"),
        median_avg_poisson_iters=("AvgPoissonIterations", "median"),
    ).reset_index()
    return tables


def scan_residual_histories(root: Path) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    history_files = sorted(root.glob("**/results/**/data/*_history.csv"))
    for path in history_files:
        # Avoid accidental huge reads from copied/archived hidden dirs if any.
        if ".git" in path.parts:
            continue
        df = safe_read_csv(path)
        if df is None:
            continue
        row: Dict[str, object] = {
            "HistoryPath": str(path.relative_to(root)),
            "HistoryFile": path.name,
            "HistoryRows": len(df),
        }
        m = re.search(r"N(?P<N>\d+)_Re(?P<Re>\d+)_(?P<Scheme>[a-zA-Z]+)_(?P<Pressure>[A-Z]+)_(?P<Impl>.+)_history\.csv$", path.name)
        if m:
            row.update({
                "N": int(m.group("N")),
                "Re": int(m.group("Re")),
                "Scheme": m.group("Scheme"),
                "PressureSolver": m.group("Pressure"),
                "ImplementationFromFile": m.group("Impl"),
            })
        for col in ["Ru", "Rv", "Rc_mass", "Rc_div", "poisson_relative_residual"]:
            if col not in df.columns:
                continue
            vals = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
            if vals.empty:
                continue
            row[f"{col}_start"] = float(vals.iloc[0])
            row[f"{col}_end"] = float(vals.iloc[-1])
            row[f"{col}_min"] = float(vals.min())
            row[f"{col}_max"] = float(vals.max())
            start = float(vals.iloc[0])
            end = float(vals.iloc[-1])
            if finite_positive(start) and finite_positive(end):
                row[f"{col}_decades_drop"] = math.log10(start / end)
        rows.append(row)
    return pd.DataFrame(rows)


def write_markdown_report(out_dir: Path, df: pd.DataFrame, grid: pd.DataFrame, tables: Dict[str, pd.DataFrame], residuals: pd.DataFrame) -> None:
    report = out_dir / "full_study_data_report.md"
    lines: List[str] = []
    lines.append("# Full Study Data Report\n")
    lines.append("This report is generated without creating image files. It summarizes the CSV outputs and identifies which plots are worth creating later.\n")
    lines.append("## What was aggregated\n")
    lines.append(f"- Total summary rows: **{len(df)}**\n")
    lines.append(f"- Residual history files: **{len(residuals)}**\n")
    lines.append(f"- Grid-convergence rows: **{len(grid)}**\n")
    if "case_counts" in tables and not tables["case_counts"].empty:
        lines.append("\n## Case counts by source\n")
        lines.append(tables["case_counts"].to_markdown(index=False))
        lines.append("\n")
    if not grid.empty:
        g = grid.dropna(subset=["ObservedOrder_combined"]).copy()
        lines.append("\n## Grid convergence from existing full-study grids\n")
        lines.append("The full mode already runs N=32,64,128. This table uses those existing results; it does not rerun extra grid cases.\n")
        if not g.empty:
            small = g[["SourceLabel", "Implementation", "Re", "Scheme", "PressureSolver", "N_coarse", "N_fine", "ObservedOrder_combined"]].head(30)
            lines.append(small.to_markdown(index=False))
            lines.append("\n")
    lines.append("\n## Recommended plots to create later\n")
    lines += [
        "1. **Validation centerlines** for selected representative cases only: Re=100, 400, 1000 with C++ serial or best-performing solver.",
        "2. **Residual-history plots** for representative cases: show Ru/Rv/Rc_mass/Rc_div decay for N=64, Re=100 and N=128, Re=1000.",
        "3. **Accuracy vs runtime Pareto plot**: combined Ghia L2 error versus runtime for each solver family.",
        "4. **Grid-convergence plot**: combined Ghia L2 error versus h using full-study N=32,64,128 data.",
        "5. **OpenMP scaling plot**: speedup/efficiency for 1,2,4,8 threads.",
        "6. **MPI case-parallel scaling plot**: wall time for full parameter sweep at 1,2,4,8 ranks.",
        "7. **Scheme/pressure comparison**: upwind vs central and RBGS vs RBSOR using runtime, residual and validation error.",
    ]
    lines.append("\n\n## Output CSV files\n")
    lines += [
        "- `all_case_summary.csv`",
        "- `casewise_relative_to_cpp_serial.csv`",
        "- `top3_fastest_per_case.csv`",
        "- `top3_lowest_error_per_case.csv`",
        "- `scheme_pressure_summary.csv`",
        "- `grid_convergence_all.csv`",
        "- `residual_history_summary.csv`",
    ]
    report.write_text("\n".join(lines), encoding="utf-8")

    candidates = out_dir / "plot_candidates_no_images_yet.md"
    candidates.write_text("\n".join([
        "# Plot Candidates — No Images Generated Yet",
        "",
        "Use these after reviewing the CSV tables.",
        "",
        "## Highest value plots",
        "- Validation U/V centerlines vs Ghia for selected cases only.",
        "- Residual decay histories for one easy case and one difficult case.",
        "- Runtime vs error Pareto comparison across solver families.",
        "- Full grid convergence from N=32,64,128 results.",
        "- OpenMP speedup and efficiency up to 8 threads.",
        "- MPI case-parallel sweep scaling up to 8 ranks.",
        "",
        "## Do not plot everything",
        "Plotting every residual and every field will flood the repo. Use the CSV report to choose representative cases first.",
    ]), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate full-study solver data without generating plots.")
    parser.add_argument("--mode", default="full", choices=["smoke", "quick", "medium", "full"])
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    root = repo_root()
    out_dir = args.out or (root / "comparison" / "results" / "data_first")
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_all_summaries(root, args.mode)
    if df.empty:
        print("No summary data found yet. Run the solver studies first.")
        return 1
    all_path = out_dir / "all_case_summary.csv"
    df.to_csv(all_path, index=False)
    print(f"Wrote {all_path}")

    grid = compute_grid_convergence(df)
    grid_path = out_dir / "grid_convergence_all.csv"
    grid.to_csv(grid_path, index=False)
    print(f"Wrote {grid_path}")

    tables = comparison_tables(df)
    for name, table in tables.items():
        path = out_dir / f"{name}.csv"
        table.to_csv(path, index=False)
        print(f"Wrote {path}")

    residuals = scan_residual_histories(root)
    residual_path = out_dir / "residual_history_summary.csv"
    residuals.to_csv(residual_path, index=False)
    print(f"Wrote {residual_path}")

    write_markdown_report(out_dir, df, grid, tables, residuals)
    print(f"Wrote {out_dir / 'full_study_data_report.md'}")
    print(f"Wrote {out_dir / 'plot_candidates_no_images_yet.md'}")
    print("Done. No image files were generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
