#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_all(repo_root: Path) -> pd.DataFrame:
    files = sorted(repo_root.glob("**/results/scaling/*.csv"))
    files = [f for f in files if "comparison/results" not in str(f)]
    frames = []
    for f in files:
        try:
            df = pd.read_csv(f)
            df["SourceFile"] = str(f.relative_to(repo_root))
            if "Solver" not in df.columns:
                df["Solver"] = f.parts[-4] if len(f.parts) >= 4 else f.parent.parent.parent.name
            frames.append(df)
        except Exception as exc:
            print(f"Skipping {f}: {exc}")
    if not frames:
        raise SystemExit("No scaling CSV files found. Run the OpenMP/MPI/CUDA scaling scripts first.")
    return pd.concat(frames, ignore_index=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Collect and plot all parallel scaling CSV files")
    ap.add_argument("--out-dir", type=Path, default=Path("comparison/results/figures/scaling"))
    ap.add_argument("--csv-out", type=Path, default=Path("comparison/results/parallel_scaling_summary.csv"))
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    df = read_all(repo_root)

    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.csv_out, index=False)

    ok = df.copy()
    if "Status" in ok.columns:
        mask = ok["Status"].astype(str).str.lower().isin(["ok", "success", "passed"])
        if mask.any():
            ok = ok.loc[mask].copy()

    if "WallTime_s" not in ok.columns and "Runtime_s" in ok.columns:
        ok["WallTime_s"] = ok["Runtime_s"]
    ok["WallTime_s"] = pd.to_numeric(ok.get("WallTime_s"), errors="coerce")
    ok["Speedup"] = pd.to_numeric(ok.get("Speedup"), errors="coerce")

    for resource in ["Threads", "Ranks", "BlockSize"]:
        if resource not in ok.columns:
            continue
        sub = ok.copy()
        sub[resource] = pd.to_numeric(sub[resource], errors="coerce")
        sub = sub.dropna(subset=[resource, "WallTime_s"])
        if sub.empty:
            continue

        fig, ax = plt.subplots(figsize=(7.5, 5.0))
        for solver, g in sub.groupby("Solver"):
            g = g.sort_values(resource)
            ax.plot(g[resource], g["WallTime_s"], marker="o", label=str(solver))
        ax.set_xlabel(resource)
        ax.set_ylabel("Wall time [s]")
        ax.set_title(f"Parallel scaling runtime vs {resource}")
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(args.out_dir / f"all_scaling_runtime_vs_{resource.lower()}.png", dpi=180)
        plt.close(fig)

        if sub["Speedup"].notna().any():
            fig, ax = plt.subplots(figsize=(7.5, 5.0))
            for solver, g in sub.groupby("Solver"):
                g = g.sort_values(resource)
                ax.plot(g[resource], g["Speedup"], marker="o", label=str(solver))
            ax.set_xlabel(resource)
            ax.set_ylabel("Speedup [-]")
            ax.set_title(f"Parallel scaling speedup vs {resource}")
            ax.grid(True, alpha=0.3)
            ax.legend()
            fig.tight_layout()
            fig.savefig(args.out_dir / f"all_scaling_speedup_vs_{resource.lower()}.png", dpi=180)
            plt.close(fig)

    print(f"Wrote {args.csv_out}")
    print(f"Wrote figures to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
