#!/usr/bin/env python3
"""
Post-processing for serial lid-driven cavity CSV outputs.

This script reads the CSV files written by src/lid_cavity.c and recreates
MATLAB-style figures:

Case-level figures:
  - velocity magnitude contour
  - pressure contour
  - streamlines
  - vorticity contour
  - velocity vectors
  - residual history
  - pressure Poisson residual history
  - Ghia centerline validation, when Re = 100, 400, or 1000

Study-level figures:
  - runtime comparison by implementation
  - pressure solver iteration comparison
  - final continuity residual by case
  - Ghia L2 error vs mesh/scheme
  - case quality summary

Example:
  python3 postprocess/plot_results.py --all-cases --summaries all
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


GHIA_DATA: Dict[int, Dict[str, np.ndarray]] = {
    100: {
        "y_u": np.array([1.0000, 0.9766, 0.9688, 0.9609, 0.9531, 0.8516, 0.7344,
                         0.6172, 0.5000, 0.4531, 0.2813, 0.1719, 0.1016, 0.0703,
                         0.0625, 0.0547, 0.0000]),
        "u": np.array([1.0000, 0.84123, 0.78871, 0.73722, 0.68717, 0.23151, 0.00332,
                       -0.13641, -0.20581, -0.21090, -0.15662, -0.10150, -0.06434,
                       -0.04775, -0.04192, -0.03717, 0.0000]),
        "x_v": np.array([1.0000, 0.9688, 0.9609, 0.9531, 0.9453, 0.9063, 0.8594,
                         0.8047, 0.5000, 0.2344, 0.2266, 0.1563, 0.0938, 0.0781,
                         0.0703, 0.0625, 0.0000]),
        "v": np.array([0.0000, -0.05906, -0.07391, -0.08864, -0.10313, -0.16914,
                       -0.22445, -0.24533, 0.05454, 0.17527, 0.17507, 0.16077,
                       0.12317, 0.10890, 0.10091, 0.09233, 0.0000]),
    },
    400: {
        "y_u": np.array([1.0000, 0.9766, 0.9688, 0.9609, 0.9531, 0.8516, 0.7344,
                         0.6172, 0.5000, 0.4531, 0.2813, 0.1719, 0.1016, 0.0703,
                         0.0625, 0.0547, 0.0000]),
        "u": np.array([1.0000, 0.75837, 0.68439, 0.61756, 0.55892, 0.29093, 0.16256,
                       0.02135, -0.11477, -0.17119, -0.32726, -0.24299, -0.14612,
                       -0.10338, -0.09266, -0.08186, 0.0000]),
        "x_v": np.array([1.0000, 0.9688, 0.9609, 0.9531, 0.9453, 0.9063, 0.8594,
                         0.8047, 0.5000, 0.2344, 0.2266, 0.1563, 0.0938, 0.0781,
                         0.0703, 0.0625, 0.0000]),
        "v": np.array([0.0000, -0.12146, -0.15663, -0.19254, -0.22847, -0.23827,
                       -0.44993, -0.38598, 0.05186, 0.30174, 0.30203, 0.28124,
                       0.22965, 0.20920, 0.19713, 0.18360, 0.0000]),
    },
    1000: {
        "y_u": np.array([1.0000, 0.9766, 0.9688, 0.9609, 0.9531, 0.8516, 0.7344,
                         0.6172, 0.5000, 0.4531, 0.2813, 0.1719, 0.1016, 0.0703,
                         0.0625, 0.0547, 0.0000]),
        "u": np.array([1.0000, 0.65928, 0.57492, 0.51117, 0.46604, 0.33304, 0.18719,
                       0.05702, -0.06080, -0.10648, -0.27805, -0.38289, -0.29730,
                       -0.22220, -0.20196, -0.18109, 0.0000]),
        "x_v": np.array([1.0000, 0.9688, 0.9609, 0.9531, 0.9453, 0.9063, 0.8594,
                         0.8047, 0.5000, 0.2344, 0.2266, 0.1563, 0.0938, 0.0781,
                         0.0703, 0.0625, 0.0000]),
        "v": np.array([0.0000, -0.21388, -0.27669, -0.33714, -0.39188, -0.51550,
                       -0.42665, -0.31966, 0.02526, 0.32235, 0.33075, 0.37095,
                       0.32627, 0.30353, 0.29012, 0.27485, 0.0000]),
    },
}


CASE_RE = re.compile(
    r"case_(?P<id>\d+)_N(?P<N>\d+)_Re(?P<Re>\d+)_(?P<scheme>[A-Za-z0-9]+)_(?P<pressure>[A-Za-z0-9]+)_(?P<implementation>[A-Za-z0-9_]+)"
)


def parse_case_name(path_or_name: str | Path) -> Dict[str, object]:
    name = Path(path_or_name).stem
    name = name.replace("_fields", "").replace("_history", "")
    match = CASE_RE.search(name)
    if not match:
        return {"case_name": name, "title": name}
    info = match.groupdict()
    info["id"] = int(info["id"])
    info["N"] = int(info["N"])
    info["Re"] = int(info["Re"])
    info["case_name"] = match.group(0)
    info["title"] = (
        f"N={info['N']} Re={info['Re']} "
        f"{info['scheme']} {info['pressure']} {info['implementation']}"
    )
    return info


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_figure(path_without_suffix: Path, dpi: int = 220) -> None:
    ensure_dir(path_without_suffix.parent)
    plt.tight_layout()
    plt.savefig(path_without_suffix.with_suffix(".png"), dpi=dpi, bbox_inches="tight")
    plt.close()


def sorted_csv_files(data_dir: Path, suffix: str) -> List[Path]:
    files = sorted(data_dir.glob(f"*{suffix}.csv"))
    return files


def latest_file(files: Iterable[Path]) -> Optional[Path]:
    files = list(files)
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def load_field_grid(field_csv: Path) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
    df = pd.read_csv(field_csv)
    required = {"i", "j", "x", "y", "u", "v", "p", "speed", "vorticity"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"{field_csv} is missing columns: {sorted(missing)}")

    x = np.sort(df["x"].unique())
    y = np.sort(df["y"].unique())

    fields: Dict[str, np.ndarray] = {}
    for col in ["u", "v", "p", "speed", "vorticity"]:
        grid = (
            df.pivot(index="i", columns="j", values=col)
            .sort_index(axis=0)
            .sort_index(axis=1)
            .to_numpy(dtype=float)
        )
        fields[col] = grid

    return x, y, fields


def plot_fields(field_csv: Path, fig_dir: Path) -> None:
    x, y, fields = load_field_grid(field_csv)
    X, Y = np.meshgrid(x, y)
    info = parse_case_name(field_csv)
    case_name = str(info["case_name"])
    title_suffix = str(info.get("title", case_name))

    contour_count = 30

    plt.figure(figsize=(7, 5.5))
    plt.contourf(X, Y, fields["speed"], levels=contour_count)
    plt.colorbar(label="Velocity magnitude")
    plt.xlim(x.min(), x.max())
    plt.ylim(y.min(), y.max())
    plt.gca().set_aspect("equal", adjustable="box")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title(f"Velocity magnitude: {title_suffix}")
    save_figure(fig_dir / f"{case_name}_speed")

    plt.figure(figsize=(7, 5.5))
    plt.contourf(X, Y, fields["p"], levels=contour_count)
    plt.colorbar(label="Pressure")
    plt.xlim(x.min(), x.max())
    plt.ylim(y.min(), y.max())
    plt.gca().set_aspect("equal", adjustable="box")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title(f"Pressure field: {title_suffix}")
    save_figure(fig_dir / f"{case_name}_pressure")

    plt.figure(figsize=(7, 5.5))
    speed = np.sqrt(fields["u"] ** 2 + fields["v"] ** 2)
    density = 1.4 if len(x) >= 48 else 1.1
    plt.streamplot(X, Y, fields["u"], fields["v"], density=density, linewidth=0.8, arrowsize=0.9)
    plt.contourf(X, Y, speed, levels=contour_count, alpha=0.25)
    plt.colorbar(label="Velocity magnitude")
    plt.xlim(x.min(), x.max())
    plt.ylim(y.min(), y.max())
    plt.gca().set_aspect("equal", adjustable="box")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title(f"Streamlines: {title_suffix}")
    save_figure(fig_dir / f"{case_name}_streamlines")

    plt.figure(figsize=(7, 5.5))
    plt.contourf(X, Y, fields["vorticity"], levels=contour_count)
    plt.colorbar(label="Vorticity")
    plt.xlim(x.min(), x.max())
    plt.ylim(y.min(), y.max())
    plt.gca().set_aspect("equal", adjustable="box")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title(f"Vorticity: {title_suffix}")
    save_figure(fig_dir / f"{case_name}_vorticity")

    plt.figure(figsize=(7, 5.5))
    skip = max(1, int(round(len(x) / 24)))
    plt.quiver(
        X[::skip, ::skip],
        Y[::skip, ::skip],
        fields["u"][::skip, ::skip],
        fields["v"][::skip, ::skip],
        angles="xy",
        scale_units="xy",
        scale=None,
        width=0.0025,
    )
    plt.xlim(x.min(), x.max())
    plt.ylim(y.min(), y.max())
    plt.gca().set_aspect("equal", adjustable="box")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title(f"Velocity vectors: {title_suffix}")
    save_figure(fig_dir / f"{case_name}_vectors")

    plot_validation(field_csv, x, y, fields, fig_dir)


def plot_history(history_csv: Path, fig_dir: Path) -> None:
    df = pd.read_csv(history_csv)
    required = {"iter", "Ru", "Rv", "Rc_mass"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"{history_csv} is missing columns: {sorted(missing)}")

    info = parse_case_name(history_csv)
    case_name = str(info["case_name"])
    title_suffix = str(info.get("title", case_name))

    plt.figure(figsize=(7, 5))
    plt.semilogy(df["iter"], df["Ru"], linewidth=1.5, label="R_u")
    plt.semilogy(df["iter"], df["Rv"], linewidth=1.5, label="R_v")
    plt.semilogy(df["iter"], df["Rc_mass"], linewidth=1.5, label="R_c mass")
    if "Rc_div" in df.columns:
        plt.semilogy(df["iter"], df["Rc_div"], linestyle="--", linewidth=1.0, label="R_c raw div")
    plt.grid(True, which="both", alpha=0.35)
    plt.xlabel("Outer iteration")
    plt.ylabel("Residual")
    plt.legend(loc="best")
    plt.title(f"Residuals: {title_suffix}")
    save_figure(fig_dir / f"{case_name}_residuals")

    if "poisson_relative_residual" in df.columns:
        plt.figure(figsize=(7, 5))
        values = df["poisson_relative_residual"].replace([np.inf, -np.inf], np.nan).dropna()
        if not values.empty:
            plt.semilogy(df.loc[values.index, "iter"], values, linewidth=1.5)
        plt.grid(True, which="both", alpha=0.35)
        plt.xlabel("Outer iteration")
        plt.ylabel("Pressure Poisson relative residual")
        plt.title(f"Pressure correction residual: {title_suffix}")
        save_figure(fig_dir / f"{case_name}_pressure_poisson_residual")


def plot_validation(field_csv: Path, x: np.ndarray, y: np.ndarray, fields: Dict[str, np.ndarray], fig_dir: Path) -> None:
    info = parse_case_name(field_csv)
    re_value = info.get("Re")
    if not isinstance(re_value, int) or re_value not in GHIA_DATA:
        return

    case_name = str(info["case_name"])
    title_suffix = str(info.get("title", case_name))
    ghia = GHIA_DATA[re_value]

    mid_j = int(np.argmin(np.abs(x - 0.5)))
    mid_i = int(np.argmin(np.abs(y - 0.5)))

    plt.figure(figsize=(6, 5.5))
    plt.plot(fields["u"][:, mid_j], y, linewidth=1.5, label="C++ solver")
    plt.plot(ghia["u"], ghia["y_u"], "o", markersize=4, label="Ghia et al.")
    plt.grid(True, alpha=0.35)
    plt.xlabel("u velocity at x = 0.5")
    plt.ylabel("y")
    plt.legend(loc="best")
    plt.title(f"Vertical centerline validation: {title_suffix}")
    save_figure(fig_dir / f"{case_name}_ghia_u")

    plt.figure(figsize=(6, 5.5))
    plt.plot(x, fields["v"][mid_i, :], linewidth=1.5, label="C++ solver")
    plt.plot(ghia["x_v"], ghia["v"], "o", markersize=4, label="Ghia et al.")
    plt.grid(True, alpha=0.35)
    plt.xlabel("x")
    plt.ylabel("v velocity at y = 0.5")
    plt.legend(loc="best")
    plt.title(f"Horizontal centerline validation: {title_suffix}")
    save_figure(fig_dir / f"{case_name}_ghia_v")


def read_summary(summary_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(summary_csv)
    for col in [
        "Runtime_s", "AvgPoissonIterations", "FinalRcMass", "Ghia_u_L2",
        "Ghia_v_L2", "CaseID", "N",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def plot_summary(summary_csv: Path, fig_dir: Path) -> None:
    df = read_summary(summary_csv)
    if df.empty:
        return

    mode = summary_csv.stem.replace("study_summary_", "")
    prefix = "study" if mode in {"quick", "medium", "full", "single"} else summary_csv.stem

    if {"Implementation", "Runtime_s"}.issubset(df.columns):
        impl = [v for v in df["Implementation"].dropna().unique()]
        plt.figure(figsize=(7, 5))
        for k, name in enumerate(impl, start=1):
            values = df.loc[df["Implementation"] == name, "Runtime_s"].dropna().to_numpy()
            if values.size == 0:
                continue
            x_values = np.full(values.shape, k, dtype=float)
            plt.plot(x_values, values, "o", markersize=5, label=str(name))
            plt.plot(k, values.mean(), "x", markersize=10, markeredgewidth=2)
        plt.grid(True, alpha=0.35)
        plt.xlim(0.5, len(impl) + 0.5)
        plt.xticks(range(1, len(impl) + 1), impl)
        plt.ylabel("Runtime [s]")
        plt.title("Runtime by implementation")
        save_figure(fig_dir / f"{prefix}_runtime_implementation")

    if {"PressureSolver", "AvgPoissonIterations"}.issubset(df.columns):
        pressure = [v for v in df["PressureSolver"].dropna().unique()]
        plt.figure(figsize=(7, 5))
        for k, name in enumerate(pressure, start=1):
            values = df.loc[df["PressureSolver"] == name, "AvgPoissonIterations"].dropna().to_numpy()
            if values.size == 0:
                continue
            x_values = np.full(values.shape, k, dtype=float)
            plt.plot(x_values, values, "o", markersize=5, label=str(name))
            plt.plot(k, values.mean(), "x", markersize=10, markeredgewidth=2)
        plt.grid(True, alpha=0.35)
        plt.xlim(0.5, len(pressure) + 0.5)
        plt.xticks(range(1, len(pressure) + 1), pressure)
        plt.ylabel("Average pressure iterations")
        plt.title("Pressure solver comparison")
        save_figure(fig_dir / f"{prefix}_pressure_solver_iterations")

    if {"CaseID", "FinalRcMass"}.issubset(df.columns):
        values = df["FinalRcMass"].replace([np.inf, -np.inf], np.nan)
        if values.notna().any():
            plt.figure(figsize=(8, 5))
            plt.semilogy(df["CaseID"], values, "o-", linewidth=1.2)
            plt.grid(True, which="both", alpha=0.35)
            plt.xlabel("Case ID")
            plt.ylabel("Final normalized mass residual")
            plt.title("Final continuity residual by case")
            save_figure(fig_dir / f"{prefix}_final_mass_residual")

    if {"Ghia_u_L2", "Scheme", "N"}.issubset(df.columns):
        valid = df["Ghia_u_L2"].notna()
        if valid.any():
            plt.figure(figsize=(7, 5))
            for scheme in df.loc[valid, "Scheme"].dropna().unique():
                data = df.loc[valid & (df["Scheme"] == scheme), ["N", "Ghia_u_L2"]].dropna()
                data = data.groupby("N", as_index=False)["Ghia_u_L2"].mean().sort_values("N")
                if not data.empty:
                    plt.plot(data["N"], data["Ghia_u_L2"], "o-", linewidth=1.5, markersize=5, label=str(scheme))
            plt.grid(True, alpha=0.35)
            plt.xlabel("Mesh size N")
            plt.ylabel("L2 error in u centerline")
            plt.legend(loc="best")
            plt.title("Mesh / scheme validation error vs Ghia")
            save_figure(fig_dir / f"{prefix}_ghia_error")

    if "Quality" in df.columns:
        counts = df["Quality"].fillna("unknown").value_counts(sort=False)
        if not counts.empty:
            plt.figure(figsize=(8, 5))
            plt.bar(np.arange(len(counts)), counts.to_numpy())
            plt.grid(True, axis="y", alpha=0.35)
            plt.xticks(np.arange(len(counts)), counts.index.to_list(), rotation=30, ha="right")
            plt.ylabel("Number of cases")
            plt.title("Case quality classification")
            save_figure(fig_dir / f"{prefix}_quality_summary")


def case_base_from_argument(case_arg: str) -> str:
    name = Path(case_arg).stem
    return name.replace("_fields", "").replace("_history", "")


def resolve_case_files(data_dir: Path, case_arg: str, all_cases: bool) -> List[Tuple[Optional[Path], Optional[Path]]]:
    field_files = sorted_csv_files(data_dir, "_fields")
    history_files = sorted_csv_files(data_dir, "_history")

    field_by_base = {case_base_from_argument(f): f for f in field_files}
    history_by_base = {case_base_from_argument(f): f for f in history_files}

    if all_cases:
        bases = sorted(set(field_by_base) | set(history_by_base))
    elif case_arg == "latest":
        latest_field = latest_file(field_files)
        latest_history = latest_file(history_files)
        candidates = [p for p in [latest_field, latest_history] if p is not None]
        if not candidates:
            return []
        base = case_base_from_argument(latest_file(candidates))
        bases = [base]
    else:
        bases = [case_base_from_argument(case_arg)]

    return [(field_by_base.get(base), history_by_base.get(base)) for base in bases]


def resolve_summary_files(data_dir: Path, summaries: str) -> List[Path]:
    summary_files = sorted(data_dir.glob("study_summary_*.csv"))
    if summaries == "none":
        return []
    if summaries == "all":
        return summary_files
    if summaries == "latest":
        latest = latest_file(summary_files)
        return [latest] if latest is not None else []
    path = Path(summaries)
    if not path.is_absolute():
        path = data_dir / path
    return [path] if path.exists() else []


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Create MATLAB-style plots from serial lid cavity CSV outputs.")
    parser.add_argument("--data-dir", default="results/data", help="Directory containing solver CSV output files.")
    parser.add_argument("--fig-dir", default="results/figures", help="Directory where PNG figures will be saved.")
    parser.add_argument("--case", default="latest", help="Case base name, a *_fields.csv/*_history.csv file, or 'latest'.")
    parser.add_argument("--all-cases", action="store_true", help="Plot every available case field/history CSV.")
    parser.add_argument("--summaries", default="latest", help="'latest', 'all', 'none', or a summary CSV file name/path.")
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir)
    fig_dir = Path(args.fig_dir)

    if not data_dir.exists():
        print(f"ERROR: data directory not found: {data_dir}", file=sys.stderr)
        return 2

    ensure_dir(fig_dir)

    case_pairs = resolve_case_files(data_dir, args.case, args.all_cases)
    summary_files = resolve_summary_files(data_dir, args.summaries)

    if not case_pairs and not summary_files:
        print(f"No matching CSV files found in {data_dir}", file=sys.stderr)
        return 1

    n_figures_before = len(list(fig_dir.glob("*.png")))

    for field_csv, history_csv in case_pairs:
        if field_csv is not None:
            print(f"Plotting fields: {field_csv}")
            plot_fields(field_csv, fig_dir)
        if history_csv is not None:
            print(f"Plotting residuals: {history_csv}")
            plot_history(history_csv, fig_dir)

    for summary_csv in summary_files:
        print(f"Plotting study summary: {summary_csv}")
        plot_summary(summary_csv, fig_dir)

    n_figures_after = len(list(fig_dir.glob("*.png")))
    print(f"Done. PNG figures are in: {fig_dir}")
    print(f"Created or updated about {max(0, n_figures_after - n_figures_before)} figure files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
