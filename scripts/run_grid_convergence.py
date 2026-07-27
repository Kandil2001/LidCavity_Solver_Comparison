#!/usr/bin/env python3
"""Run a small grid-convergence study and estimate observed order of accuracy.

The script runs one serial solver on progressively finer meshes, reads the
solver summary CSV files, and computes the observed order using the Ghia
centerline L2 errors:

    p = log(e_coarse / e_fine) / log(h_coarse / h_fine)

This is a practical portfolio-level convergence check. It is not a substitute
for a manufactured-solution study because the reference data are benchmark
centerline values, not an exact analytical solution.

Examples from the repository root:

    python3 scripts/run_grid_convergence.py --solver cpp --N-list 32,64,128
    python3 scripts/run_grid_convergence.py --solver python --implementation serial_python_vectorized --N-list 32,64
"""
from __future__ import annotations

import argparse
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


@dataclass(frozen=True)
class SolverSpec:
    name: str
    folder: Path
    build_cmd: Optional[List[str]]
    run_cmd: List[str]
    default_implementation: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def solver_specs(root: Path, python_exe: str) -> Dict[str, SolverSpec]:
    return {
        "python": SolverSpec(
            name="python",
            folder=root / "python" / "serial",
            build_cmd=None,
            run_cmd=[python_exe, "src/lid_cavity.py"],
            default_implementation="serial_python_vectorized",
        ),
        "c": SolverSpec(
            name="c",
            folder=root / "c" / "serial",
            build_cmd=["make", "build"],
            run_cmd=["./bin/lid_cavity_c"],
            default_implementation="serial_c",
        ),
        "cpp": SolverSpec(
            name="cpp",
            folder=root / "cpp" / "serial",
            build_cmd=["make", "build"],
            run_cmd=["./bin/lid_cavity"],
            default_implementation="serial_cpp",
        ),
    }


def parse_n_list(raw: str) -> List[int]:
    values = [int(x.strip()) for x in raw.split(",") if x.strip()]
    if len(values) < 2:
        raise argparse.ArgumentTypeError("Provide at least two grid sizes, for example 32,64,128")
    if len(set(values)) != len(values):
        raise argparse.ArgumentTypeError("Grid sizes must be unique")
    if any(n < 4 for n in values):
        raise argparse.ArgumentTypeError("Grid sizes should be at least 4")
    return sorted(values)


def run_command(cmd: List[str], cwd: Path, dry_run: bool = False) -> None:
    printable = " ".join(cmd)
    print(f"$ (cd {cwd} && {printable})", flush=True)
    if dry_run:
        return
    subprocess.run(cmd, cwd=cwd, check=True)


def read_single_summary(spec: SolverSpec) -> pd.Series:
    path = spec.folder / "results" / "data" / "study_summary_single.csv"
    if not path.exists():
        raise FileNotFoundError(f"Expected summary not found: {path}")
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError(f"Summary file is empty: {path}")
    return df.iloc[-1].copy()


def finite_positive(value: object) -> bool:
    try:
        x = float(value)
    except Exception:
        return False
    return math.isfinite(x) and x > 0.0


def add_order_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("N").copy()
    df["h"] = 1.0 / (df["N"].astype(float) - 1.0)
    df["Ghia_combined_L2"] = np.sqrt(df["Ghia_u_L2"] ** 2 + df["Ghia_v_L2"] ** 2)

    for err_col, out_col in [
        ("Ghia_u_L2", "Order_u_from_previous"),
        ("Ghia_v_L2", "Order_v_from_previous"),
        ("Ghia_combined_L2", "Order_combined_from_previous"),
    ]:
        orders: List[float] = [math.nan]
        for i in range(1, len(df)):
            e0 = df.iloc[i - 1][err_col]
            e1 = df.iloc[i][err_col]
            h0 = df.iloc[i - 1]["h"]
            h1 = df.iloc[i]["h"]
            if finite_positive(e0) and finite_positive(e1) and finite_positive(h0) and finite_positive(h1) and h0 != h1:
                orders.append(math.log(float(e0) / float(e1)) / math.log(float(h0) / float(h1)))
            else:
                orders.append(math.nan)
        df[out_col] = orders
    return df


def plot_convergence(df: pd.DataFrame, out_dir: Path, stem: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(7.2, 5.0))
    for col, label in [("Ghia_u_L2", "u centerline L2"), ("Ghia_v_L2", "v centerline L2"), ("Ghia_combined_L2", "combined L2")]:
        sub = df[["h", col]].replace([np.inf, -np.inf], np.nan).dropna()
        sub = sub[sub[col] > 0]
        if not sub.empty:
            plt.loglog(sub["h"], sub[col], "o-", label=label)
    plt.gca().invert_xaxis()
    plt.grid(True, which="both", alpha=0.35)
    plt.xlabel("Grid spacing h = 1/(N-1)")
    plt.ylabel("L2 error vs Ghia centerline data")
    plt.title("Grid convergence against Ghia benchmark data")
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(out_dir / f"{stem}_errors.png", dpi=180)
    plt.close()

    order_cols = ["Order_u_from_previous", "Order_v_from_previous", "Order_combined_from_previous"]
    valid = df[["N", *order_cols]].dropna(how="all", subset=order_cols)
    if not valid.empty:
        plt.figure(figsize=(7.2, 5.0))
        for col in order_cols:
            sub = valid[["N", col]].dropna()
            if not sub.empty:
                plt.plot(sub["N"], sub[col], "o-", label=col.replace("Order_", "").replace("_from_previous", ""))
        plt.grid(True, alpha=0.35)
        plt.xlabel("Fine-grid N")
        plt.ylabel("Observed order from previous grid")
        plt.title("Observed order of accuracy")
        plt.legend(loc="best")
        plt.tight_layout()
        plt.savefig(out_dir / f"{stem}_orders.png", dpi=180)
        plt.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a grid convergence study for a serial solver.")
    parser.add_argument("--solver", choices=["python", "c", "cpp"], default="cpp")
    parser.add_argument("--N-list", type=parse_n_list, default=parse_n_list("32,64,128"))
    parser.add_argument("--Re", type=int, default=100)
    parser.add_argument("--scheme", default="upwind", help="upwind is the most robust default for a quick convergence check")
    parser.add_argument("--pressure", default="RBGS")
    parser.add_argument("--implementation", default=None, help="Override implementation label, for example serial_python_looped")
    parser.add_argument("--maxIter", type=int, default=None, help="Optional solver iteration override")
    parser.add_argument("--poisson-maxIter", type=int, default=None, help="Optional pressure-iteration override")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = repo_root()
    specs = solver_specs(root, args.python)
    spec = specs[args.solver]
    implementation = args.implementation or spec.default_implementation

    if spec.build_cmd is not None:
        run_command(spec.build_cmd, spec.folder, dry_run=args.dry_run)

    rows = []
    for n in args.N_list:
        cmd = [
            *spec.run_cmd,
            "--single",
            "--N", str(n),
            "--Re", str(args.Re),
            "--scheme", args.scheme,
            "--pressure", args.pressure,
            "--implementation", implementation,
            "--no-fields",
        ]
        if args.maxIter is not None:
            cmd += ["--maxIter", str(args.maxIter)]
        if args.poisson_maxIter is not None:
            cmd += ["--poisson-maxIter", str(args.poisson_maxIter)]
        run_command(cmd, spec.folder, dry_run=args.dry_run)
        if not args.dry_run:
            row = read_single_summary(spec)
            row["Solver"] = spec.name
            rows.append(row)

    if args.dry_run:
        return 0

    df = pd.DataFrame(rows)
    numeric_cols = ["N", "Re", "Runtime_s", "Ghia_u_L2", "Ghia_v_L2", "Ghia_u_Linf", "Ghia_v_Linf"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = add_order_columns(df)

    out_dir = root / "comparison" / "results" / "grid_convergence"
    safe_impl = implementation.replace("/", "_")
    stem = f"grid_convergence_{args.solver}_Re{args.Re}_{args.scheme}_{args.pressure}_{safe_impl}"
    out_csv = out_dir / f"{stem}.csv"
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    plot_convergence(df, out_dir, stem)

    print(f"\nWrote {out_csv}")
    print(f"Wrote plots to {out_dir}")
    print(df[["Solver", "Implementation", "N", "Re", "Ghia_u_L2", "Ghia_v_L2", "Order_u_from_previous", "Order_v_from_previous"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
