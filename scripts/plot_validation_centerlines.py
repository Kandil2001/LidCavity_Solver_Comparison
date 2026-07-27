#!/usr/bin/env python3
"""Create automatic Ghia centerline validation plots from solver field CSV files.

Run from the repository root after one or more solver runs have written
``*_fields.csv`` files:

    python3 scripts/plot_validation_centerlines.py --Re 100 --N 64
    python3 scripts/plot_validation_centerlines.py --Re 400 --scheme central --pressure RBGS

The script scans all solver result folders, extracts u(x=0.5,y) and
v(x,y=0.5), and overlays them against the Ghia et al. benchmark data.
"""
from __future__ import annotations

import argparse
import re
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
    r"case_(?P<id>\d+)_N(?P<N>\d+)_Re(?P<Re>\d+)_(?P<scheme>[A-Za-z0-9]+)_(?P<pressure>[A-Za-z0-9]+)_(?P<implementation>[A-Za-z0-9_]+)_fields$"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_case(path: Path) -> Optional[Dict[str, object]]:
    m = CASE_RE.search(path.stem)
    if not m:
        return None
    info: Dict[str, object] = m.groupdict()
    info["id"] = int(info["id"])
    info["N"] = int(info["N"])
    info["Re"] = int(info["Re"])
    info["scheme"] = str(info["scheme"]).lower()
    info["pressure"] = str(info["pressure"]).upper()
    return info


def solver_label(root: Path, path: Path, implementation: str) -> str:
    rel = path.relative_to(root)
    parts = rel.parts
    if len(parts) >= 3:
        prefix = "/".join(parts[:2])
    else:
        prefix = parts[0]
    return f"{prefix}: {implementation}"


def load_centerlines(field_csv: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    df = pd.read_csv(field_csv)
    required = {"x", "y", "u", "v"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{field_csv} is missing columns: {sorted(missing)}")

    x = np.sort(df["x"].unique())
    y = np.sort(df["y"].unique())
    u = df.pivot(index="i", columns="j", values="u").sort_index(axis=0).sort_index(axis=1).to_numpy(dtype=float)
    v = df.pivot(index="i", columns="j", values="v").sort_index(axis=0).sort_index(axis=1).to_numpy(dtype=float)

    mid_j = int(np.argmin(np.abs(x - 0.5)))
    mid_i = int(np.argmin(np.abs(y - 0.5)))
    return y, u[:, mid_j], x, v[mid_i, :]


def matching_files(root: Path, args: argparse.Namespace) -> List[Path]:
    files = []
    for path in root.rglob("*_fields.csv"):
        if "results" not in path.parts or "data" not in path.parts:
            continue
        info = parse_case(path)
        if not info:
            continue
        if int(info["Re"]) != args.Re:
            continue
        if args.N is not None and int(info["N"]) != args.N:
            continue
        if args.scheme and str(info["scheme"]).lower() != args.scheme.lower():
            continue
        if args.pressure and str(info["pressure"]).upper() != args.pressure.upper():
            continue
        files.append(path)
    files.sort(key=lambda p: (str(p.parent.parent.parent), p.stat().st_mtime), reverse=True)
    return files[: args.max_curves]


def make_plots(root: Path, files: List[Path], args: argparse.Namespace) -> None:
    if args.Re not in GHIA_DATA:
        raise SystemExit(f"No Ghia data bundled for Re={args.Re}. Use 100, 400, or 1000.")
    ghia = GHIA_DATA[args.Re]
    out_dir = root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    setup_bits = [f"Re{args.Re}"]
    if args.N is not None:
        setup_bits.append(f"N{args.N}")
    if args.scheme:
        setup_bits.append(args.scheme.lower())
    if args.pressure:
        setup_bits.append(args.pressure.upper())
    stem = "validation_centerlines_" + "_".join(setup_bits)

    plt.figure(figsize=(7.2, 5.6))
    for path in files:
        info = parse_case(path)
        if not info:
            continue
        y, u_mid, _, _ = load_centerlines(path)
        plt.plot(u_mid, y, linewidth=1.4, label=solver_label(root, path, str(info["implementation"])))
    plt.plot(ghia["u"], ghia["y_u"], "o", markersize=4, label="Ghia benchmark")
    plt.grid(True, alpha=0.35)
    plt.xlabel("u velocity at x = 0.5")
    plt.ylabel("y")
    plt.title(f"Vertical centerline validation, Re={args.Re}")
    plt.legend(loc="best", fontsize=8)
    plt.tight_layout()
    plt.savefig(out_dir / f"{stem}_u.png", dpi=180)
    plt.close()

    plt.figure(figsize=(7.2, 5.6))
    for path in files:
        info = parse_case(path)
        if not info:
            continue
        _, _, x, v_mid = load_centerlines(path)
        plt.plot(x, v_mid, linewidth=1.4, label=solver_label(root, path, str(info["implementation"])))
    plt.plot(ghia["x_v"], ghia["v"], "o", markersize=4, label="Ghia benchmark")
    plt.grid(True, alpha=0.35)
    plt.xlabel("x")
    plt.ylabel("v velocity at y = 0.5")
    plt.title(f"Horizontal centerline validation, Re={args.Re}")
    plt.legend(loc="best", fontsize=8)
    plt.tight_layout()
    plt.savefig(out_dir / f"{stem}_v.png", dpi=180)
    plt.close()

    print(f"Plotted {len(files)} solver field files")
    print(f"Wrote {out_dir / (stem + '_u.png')}")
    print(f"Wrote {out_dir / (stem + '_v.png')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot Ghia U/V centerline validation from solver field CSV files.")
    parser.add_argument("--Re", type=int, default=100, choices=[100, 400, 1000])
    parser.add_argument("--N", type=int, default=None, help="Optional grid size filter")
    parser.add_argument("--scheme", default=None, help="Optional scheme filter, e.g. upwind or central")
    parser.add_argument("--pressure", default=None, help="Optional pressure solver filter, e.g. RBGS or RBSOR")
    parser.add_argument("--max-curves", type=int, default=8, help="Maximum number of solver curves to overlay")
    parser.add_argument("--out-dir", type=Path, default=Path("comparison/results/figures/validation"))
    args = parser.parse_args()

    root = repo_root()
    files = matching_files(root, args)
    if not files:
        raise SystemExit("No matching *_fields.csv files found. Run at least one solver without --no-fields first.")
    make_plots(root, files, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
