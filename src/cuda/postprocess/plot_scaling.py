#!/usr/bin/env python3
"""Plot strong-scaling benchmark results.

This script reads CSV files produced by the scaling scripts and creates:
- runtime vs resource count
- speedup vs resource count
- efficiency vs resource count
"""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


def _resource_column(df: pd.DataFrame) -> str:
    for col in ["Threads", "Ranks", "BlockSize"]:
        if col in df.columns:
            vals = pd.to_numeric(df[col], errors="coerce")
            if vals.notna().any():
                return col
    raise SystemExit("Could not find Threads, Ranks, or BlockSize column in scaling CSV")


def _status_filter(df: pd.DataFrame) -> pd.DataFrame:
    if "Status" in df.columns:
        ok = df["Status"].astype(str).str.lower().isin(["ok", "success", "passed"])
        if ok.any():
            return df.loc[ok].copy()
    return df.copy()


def _numeric(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce")


def make_plots(csv_path: Path, out_dir: Path) -> None:
    df = pd.read_csv(csv_path)
    df = _status_filter(df)
    if df.empty:
        raise SystemExit(f"No successful rows found in {csv_path}")
    resource = _resource_column(df)
    df[resource] = _numeric(df, resource)
    df["WallTime_s"] = _numeric(df, "WallTime_s")
    if "Speedup" not in df.columns or df["Speedup"].isna().all():
        base = df.sort_values(resource).iloc[0]["WallTime_s"]
        df["Speedup"] = base / df["WallTime_s"]
    else:
        df["Speedup"] = _numeric(df, "Speedup")
    if "Efficiency" not in df.columns or df["Efficiency"].isna().all():
        base_resource = df.sort_values(resource).iloc[0][resource]
        df["Efficiency"] = df["Speedup"] / (df[resource] / base_resource)
    else:
        df["Efficiency"] = _numeric(df, "Efficiency")

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = csv_path.stem
    for ycol, ylabel, suffix in [
        ("WallTime_s", "Wall time [s]", "runtime"),
        ("Speedup", "Speedup [-]", "speedup"),
        ("Efficiency", "Parallel efficiency [-]", "efficiency"),
    ]:
        fig, ax = plt.subplots(figsize=(7.2, 4.8))
        ax.plot(df[resource], df[ycol], marker="o")
        ax.set_xlabel(resource)
        ax.set_ylabel(ylabel)
        ax.set_title(f"{stem}: {suffix}")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(out_dir / f"{stem}_{suffix}.png", dpi=180)
        plt.close(fig)


def main() -> int:
    p = argparse.ArgumentParser(description="Plot scaling CSV files")
    p.add_argument("csv", type=Path, help="Path to scaling CSV")
    p.add_argument("--out", type=Path, default=Path("results/figures/scaling"), help="Output figure directory")
    args = p.parse_args()
    make_plots(args.csv, args.out)
    print(f"Wrote scaling plots to {args.out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
