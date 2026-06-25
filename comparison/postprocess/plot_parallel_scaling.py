#!/usr/bin/env python3
"""Collect and plot OpenMP/MPI/CUDA scaling CSV files.

The expected CSV columns are flexible, but the most useful columns are:

    Solver, Method, Threads or Ranks, WallTime_s, Speedup, Efficiency, Status

Use from the repository root:

    python3 comparison/postprocess/plot_parallel_scaling.py
    python3 comparison/postprocess/plot_parallel_scaling.py --input comparison/results/scaling/parallel_scaling_summary.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_all(repo_root: Path, input_files: List[Path]) -> pd.DataFrame:
    if input_files:
        files = [p if p.is_absolute() else repo_root / p for p in input_files]
    else:
        files = sorted(repo_root.glob("**/results/scaling/*.csv"))
        files = [f for f in files if "comparison/results/figures" not in str(f)]
    frames = []
    for f in files:
        if not f.exists():
            print(f"Skipping missing scaling file: {f}")
            continue
        try:
            df = pd.read_csv(f)
            if df.empty:
                continue
            df["SourceFile"] = str(f.relative_to(repo_root)) if f.is_relative_to(repo_root) else str(f)
            if "Solver" not in df.columns:
                # For files inside c/openmp/results/scaling etc., use the path as a readable fallback.
                parts = f.relative_to(repo_root).parts if f.is_relative_to(repo_root) else f.parts
                df["Solver"] = "/".join(parts[:2]) if len(parts) >= 2 else f.stem
            frames.append(df)
        except Exception as exc:
            print(f"Skipping {f}: {exc}")
    if not frames:
        raise SystemExit("No scaling CSV files found. Run scripts/run_parallel_scaling.py first.")
    return pd.concat(frames, ignore_index=True)


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    ok = df.copy()
    if "Status" in ok.columns:
        mask = ok["Status"].astype(str).str.lower().isin(["ok", "success", "passed"])
        if mask.any():
            ok = ok.loc[mask].copy()

    if "WallTime_s" not in ok.columns and "Runtime_s" in ok.columns:
        ok["WallTime_s"] = ok["Runtime_s"]
    if "WallTime_s" not in ok.columns:
        raise SystemExit("Scaling CSV needs WallTime_s or Runtime_s.")

    ok["WallTime_s"] = pd.to_numeric(ok["WallTime_s"], errors="coerce")
    for col in ["Threads", "Ranks", "BlockSize", "Speedup", "Efficiency"]:
        if col in ok.columns:
            ok[col] = pd.to_numeric(ok[col], errors="coerce")
    return ok


def add_missing_metrics(sub: pd.DataFrame, resource: str) -> pd.DataFrame:
    out = sub.copy().sort_values(resource)
    if out.empty:
        return out
    if "Speedup" not in out.columns:
        out["Speedup"] = float("nan")
    if "Efficiency" not in out.columns:
        out["Efficiency"] = float("nan")
    if out["Speedup"].isna().all():
        base = out.iloc[0]
        base_time = float(base["WallTime_s"])
        base_resource = float(base[resource])
        if base_time > 0 and base_resource > 0:
            out["Speedup"] = base_time / out["WallTime_s"]
            out["Efficiency"] = out["Speedup"] / (out[resource] / base_resource)
    elif out["Efficiency"].isna().all():
        base_resource = float(out.iloc[0][resource])
        if base_resource > 0:
            out["Efficiency"] = out["Speedup"] / (out[resource] / base_resource)
    return out


def plot_by_resource(df: pd.DataFrame, resource: str, out_dir: Path) -> None:
    if resource not in df.columns:
        return
    sub = df.dropna(subset=[resource, "WallTime_s"]).copy()
    if sub.empty:
        return
    sub[resource] = pd.to_numeric(sub[resource], errors="coerce")
    sub = sub.dropna(subset=[resource])
    if sub.empty:
        return

    group_cols = ["Solver"]
    if "Method" in sub.columns:
        group_cols.append("Method")

    enriched = []
    for _, g in sub.groupby(group_cols, dropna=False):
        enriched.append(add_missing_metrics(g, resource))
    sub = pd.concat(enriched, ignore_index=True)

    plots = [
        ("WallTime_s", "Wall time [s]", "runtime"),
        ("Speedup", "Speedup [-]", "speedup"),
        ("Efficiency", "Parallel efficiency [-]", "efficiency"),
    ]
    for ycol, ylabel, suffix in plots:
        if ycol not in sub.columns or sub[ycol].isna().all():
            continue
        fig, ax = plt.subplots(figsize=(7.5, 5.0))
        for solver, g in sub.groupby("Solver"):
            g = g.sort_values(resource)
            ax.plot(g[resource], g[ycol], marker="o", label=str(solver))
        ax.set_xlabel(resource)
        ax.set_ylabel(ylabel)
        ax.set_title(f"Parallel scaling {suffix} vs {resource}")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best")
        fig.tight_layout()
        fig.savefig(out_dir / f"all_scaling_{suffix}_vs_{resource.lower()}.png", dpi=180)
        plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser(description="Collect and plot all parallel scaling CSV files")
    ap.add_argument("--input", type=Path, action="append", default=[], help="Optional scaling CSV file. Can be used multiple times.")
    ap.add_argument("--out-dir", type=Path, default=Path("comparison/results/figures/scaling"))
    ap.add_argument("--csv-out", type=Path, default=Path("comparison/results/scaling/parallel_scaling_collected.csv"))
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    df = prepare(read_all(repo_root, args.input))

    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.csv_out, index=False)

    for resource in ["Threads", "Ranks", "BlockSize"]:
        plot_by_resource(df, resource, args.out_dir)

    print(f"Wrote {args.csv_out}")
    print(f"Wrote figures to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
