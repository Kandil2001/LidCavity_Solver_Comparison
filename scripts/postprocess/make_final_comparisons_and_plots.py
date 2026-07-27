#!/usr/bin/env python3

from pathlib import Path
import re
import math
import pandas as pd

BASE = Path("comparison/results/strong_scaling_parts")
FINAL = Path("comparison/results/final_cpu_cuda_merged")
TABLES = FINAL / "comparisons"
FIGS = FINAL / "figures"

TABLES.mkdir(parents=True, exist_ok=True)
FIGS.mkdir(parents=True, exist_ok=True)

CUDA = Path("cuda_a100_results/cpu_exact_full_validated/saved_runs/cuda_cpu_exact_full_A100_21180878/cuda_full_summary_validated.csv")
CASE_LIST = Path("case_list_domain.txt")


def find_col(df, names):
    lower = {str(c).lower(): c for c in df.columns}
    for n in names:
        if n in df.columns:
            return n
        if n.lower() in lower:
            return lower[n.lower()]
    return None


def runtime_column(df):
    preferred = [
        "runtime_s", "Runtime_s", "Runtime", "runtime",
        "time_s", "elapsed_s", "wall_time_s",
        "execution_time_s", "total_time_s"
    ]
    col = find_col(df, preferred)
    if col:
        return col

    for c in df.columns:
        cl = str(c).lower()
        if ("runtime" in cl or "elapsed" in cl or "wall" in cl) and "timestamp" not in cl:
            return c

    return None


def case_from_folder(name):
    m = re.search(r"_case_(\d+)$", name)
    return int(m.group(1)) if m else None


def case_map_from_file():
    mapping = {}
    if not CASE_LIST.exists():
        return mapping

    i = 0
    for line in CASE_LIST.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        i += 1
        parts = line.split(":")
        if len(parts) >= 5:
            try:
                N = int(parts[0])
                Re = int(parts[1])
                scheme = parts[2]
                mapping[(N, Re, scheme)] = i
            except Exception:
                pass

    return mapping


CASE_MAP = case_map_from_file()


def add_case_index_from_columns(df):
    df = df.copy()

    if "CaseIndex" in df.columns:
        df["case"] = pd.to_numeric(df["CaseIndex"], errors="coerce")
        return df

    ncol = find_col(df, ["N", "n"])
    recol = find_col(df, ["Re", "RE", "re"])
    schemecol = find_col(df, ["scheme", "Scheme"])

    if ncol and recol and schemecol:
        def lookup(row):
            try:
                return CASE_MAP.get((int(row[ncol]), int(row[recol]), str(row[schemecol])))
            except Exception:
                return None

        df["case"] = df.apply(lookup, axis=1)
        return df

    def parse_any(row):
        text = ",".join(str(x) for x in row.values)
        m = re.search(r"case(\d+)_", text)
        if m:
            return int(m.group(1))
        return None

    df["case"] = df.apply(parse_any, axis=1)
    return df


def svg_escape(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write_bar_svg(path, title, labels, values, ylabel="Value", log=False):
    width = 950
    height = 520
    left = 95
    right = 30
    top = 70
    bottom = 120
    plot_w = width - left - right
    plot_h = height - top - bottom

    vals = [float(v) if pd.notna(v) else 0.0 for v in values]
    if log:
        vals_plot = [math.log10(max(v, 1e-9)) for v in vals]
        ymax = max(vals_plot) if vals_plot else 1
        ymin = min(vals_plot) if vals_plot else 0
        if ymax == ymin:
            ymax += 1
    else:
        vals_plot = vals
        ymin = 0
        ymax = max(vals_plot) * 1.15 if vals_plot and max(vals_plot) > 0 else 1

    n = max(len(labels), 1)
    gap = 12
    bar_w = max(8, (plot_w - gap * (n + 1)) / n)

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append(f'<text x="{width/2}" y="35" text-anchor="middle" font-family="Arial" font-size="22" font-weight="bold">{svg_escape(title)}</text>')
    parts.append(f'<text x="20" y="{top + plot_h/2}" text-anchor="middle" transform="rotate(-90 20 {top + plot_h/2})" font-family="Arial" font-size="14">{svg_escape(ylabel)}</text>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="black"/>')
    parts.append(f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="black"/>')

    for i, (lab, val, vp) in enumerate(zip(labels, vals, vals_plot)):
        x = left + gap + i * (bar_w + gap)
        if log:
            y = top + plot_h - ((vp - ymin) / (ymax - ymin)) * plot_h
        else:
            y = top + plot_h - (vp / ymax) * plot_h
        h = top + plot_h - y
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="#4C78A8"/>')
        parts.append(f'<text x="{x + bar_w/2:.1f}" y="{y - 6:.1f}" text-anchor="middle" font-family="Arial" font-size="11">{val:.3g}</text>')
        parts.append(f'<text x="{x + bar_w/2:.1f}" y="{top+plot_h+18}" text-anchor="end" transform="rotate(-45 {x + bar_w/2:.1f} {top+plot_h+18})" font-family="Arial" font-size="12">{svg_escape(lab)}</text>')

    parts.append('</svg>')
    path.write_text("\n".join(parts))


def write_line_svg(path, title, df, xcol, ycol, groupcol, ylabel="Runtime [s]", log=True):
    width = 1050
    height = 620
    left = 95
    right = 180
    top = 70
    bottom = 80
    plot_w = width - left - right
    plot_h = height - top - bottom

    d = df[[xcol, ycol, groupcol]].dropna().copy()
    d[xcol] = pd.to_numeric(d[xcol], errors="coerce")
    d[ycol] = pd.to_numeric(d[ycol], errors="coerce")
    d = d.dropna()

    if d.empty:
        path.write_text("<svg xmlns='http://www.w3.org/2000/svg'><text x='20' y='30'>No data</text></svg>")
        return

    xs = sorted(d[xcol].unique())
    yvals = d[ycol].tolist()

    if log:
        y_plot_vals = [math.log10(max(float(v), 1e-9)) for v in yvals]
        ymin = min(y_plot_vals)
        ymax = max(y_plot_vals)
    else:
        ymin = 0
        ymax = max(yvals)

    if ymax == ymin:
        ymax += 1

    xmin = min(xs)
    xmax = max(xs)
    if xmax == xmin:
        xmax += 1

    def x_map(x):
        return left + ((x - xmin) / (xmax - xmin)) * plot_w

    def y_map(y):
        yy = math.log10(max(float(y), 1e-9)) if log else float(y)
        return top + plot_h - ((yy - ymin) / (ymax - ymin)) * plot_h

    colors = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#B279A2"]

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append(f'<text x="{width/2}" y="35" text-anchor="middle" font-family="Arial" font-size="22" font-weight="bold">{svg_escape(title)}</text>')
    parts.append(f'<text x="20" y="{top + plot_h/2}" text-anchor="middle" transform="rotate(-90 20 {top + plot_h/2})" font-family="Arial" font-size="14">{svg_escape(ylabel)}</text>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="black"/>')
    parts.append(f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="black"/>')

    for x in xs:
        xx = x_map(x)
        parts.append(f'<line x1="{xx:.1f}" y1="{top+plot_h}" x2="{xx:.1f}" y2="{top+plot_h+6}" stroke="black"/>')
        parts.append(f'<text x="{xx:.1f}" y="{top+plot_h+24}" text-anchor="middle" font-family="Arial" font-size="12">{int(x)}</text>')

    groups = list(d[groupcol].dropna().unique())
    for gi, g in enumerate(groups):
        sub = d[d[groupcol] == g].sort_values(xcol)
        color = colors[gi % len(colors)]
        pts = [(x_map(float(r[xcol])), y_map(float(r[ycol]))) for _, r in sub.iterrows()]
        if len(pts) >= 2:
            point_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
            parts.append(f'<polyline points="{point_str}" fill="none" stroke="{color}" stroke-width="3"/>')
        for x, y in pts:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/>')
        ly = top + 25 + gi * 24
        parts.append(f'<rect x="{left+plot_w+25}" y="{ly-12}" width="14" height="14" fill="{color}"/>')
        parts.append(f'<text x="{left+plot_w+45}" y="{ly}" font-family="Arial" font-size="13">{svg_escape(g)}</text>')

    parts.append(f'<text x="{left+plot_w/2}" y="{height-25}" text-anchor="middle" font-family="Arial" font-size="14">Case index</text>')
    parts.append('</svg>')
    path.write_text("\n".join(parts))


# ----------------------------
# CPU data
# ----------------------------

status_rows = []
cpu_success = []

for family in ["openmp", "mpi", "hybrid"]:
    folders = sorted(BASE.glob(f"{family}_case_*"), key=lambda p: case_from_folder(p.name) or 999)

    for folder in folders:
        raw = folder / "strong_scaling_raw.csv"
        summary = folder / "strong_scaling_summary.csv"
        best = folder / "strong_scaling_best_by_solver.csv"
        report = folder / "strong_scaling_report.md"
        case = case_from_folder(folder.name)

        row = {
            "family": family,
            "case": case,
            "raw_exists": raw.exists(),
            "summary_exists": summary.exists(),
            "best_exists": best.exists(),
            "report_exists": report.exists(),
            "raw_rows": 0,
            "success_rows": 0,
            "failed_rows": 0,
            "salvaged_case": family in ["mpi", "hybrid"] and case == 13,
        }

        if raw.exists():
            df = pd.read_csv(raw)
            row["raw_rows"] = len(df)

            status_col = find_col(df, ["status"])
            rt_col = runtime_column(df)

            if status_col:
                counts = df[status_col].astype(str).str.lower().value_counts()
                row["success_rows"] = int(counts.get("success", 0))
                row["failed_rows"] = int(counts.get("failed", 0))
                ok = df[df[status_col].astype(str).str.lower() == "success"].copy()
            else:
                ok = df.copy()

            if rt_col:
                ok["Runtime_s"] = pd.to_numeric(ok[rt_col], errors="coerce")
                ok = ok.dropna(subset=["Runtime_s"])
                ok.insert(0, "family", family)
                ok.insert(1, "case", case)
                cpu_success.append(ok)

        status_rows.append(row)

status = pd.DataFrame(status_rows)
status.to_csv(TABLES / "cpu_completeness_status.csv", index=False)

completion = status.groupby("family")[["success_rows", "failed_rows"]].sum().reset_index()
completion.to_csv(TABLES / "cpu_success_failed_overview.csv", index=False)

cpu = pd.concat(cpu_success, ignore_index=True) if cpu_success else pd.DataFrame()
cpu.to_csv(TABLES / "cpu_successful_runtime_rows.csv", index=False)

if not cpu.empty:
    cpu_best = cpu.groupby(["family", "case"])["Runtime_s"].min().reset_index()
    cpu_best = cpu_best.rename(columns={"Runtime_s": "best_runtime_s"})
    cpu_best.to_csv(TABLES / "cpu_best_runtime_by_case.csv", index=False)
else:
    cpu_best = pd.DataFrame()

# ----------------------------
# CUDA data
# ----------------------------

if CUDA.exists():
    cuda = pd.read_csv(CUDA)
    cuda = add_case_index_from_columns(cuda)
    rt_col = runtime_column(cuda)

    if rt_col:
        cuda["Runtime_s"] = pd.to_numeric(cuda[rt_col], errors="coerce")
    else:
        cuda["Runtime_s"] = pd.NA

    cuda.to_csv(TABLES / "cuda_full_rbgs_rbsor_rows.csv", index=False)

    pressure_col = find_col(cuda, ["PressureSolver", "pressure_solver", "poisson_solver"])
    if pressure_col:
        cuda_solver = cuda.groupby(pressure_col)["Runtime_s"].agg(["count", "min", "mean", "median", "max"]).reset_index()
        cuda_solver.to_csv(TABLES / "cuda_runtime_by_pressure_solver.csv", index=False)
    else:
        cuda_solver = pd.DataFrame()

    if "case" in cuda.columns:
        cuda_best = cuda.dropna(subset=["Runtime_s", "case"]).groupby("case")["Runtime_s"].min().reset_index()
        cuda_best = cuda_best.rename(columns={"Runtime_s": "best_runtime_s"})
        cuda_best.to_csv(TABLES / "cuda_best_runtime_by_case.csv", index=False)
    else:
        cuda_best = pd.DataFrame()
else:
    cuda = pd.DataFrame()
    cuda_solver = pd.DataFrame()
    cuda_best = pd.DataFrame()

# ----------------------------
# Combined best
# ----------------------------

combined = []

if not cpu_best.empty:
    a = cpu_best.copy()
    a["backend"] = a["family"].map({
        "openmp": "CPU OpenMP",
        "mpi": "CPU MPI",
        "hybrid": "CPU Hybrid"
    })
    combined.append(a[["backend", "case", "best_runtime_s"]])

if not cuda_best.empty:
    b = cuda_best.copy()
    b["backend"] = "CUDA A100"
    combined.append(b[["backend", "case", "best_runtime_s"]])

if combined:
    combined_best = pd.concat(combined, ignore_index=True)
    combined_best.to_csv(TABLES / "combined_best_runtime_by_case_backend.csv", index=False)
else:
    combined_best = pd.DataFrame()

# ----------------------------
# SVG plots
# ----------------------------

write_bar_svg(
    FIGS / "cpu_success_failed_overview.svg",
    "CPU successful rows by backend",
    completion["family"].tolist(),
    completion["success_rows"].tolist(),
    ylabel="Successful rows",
    log=False
)

if not cpu_best.empty:
    write_line_svg(
        FIGS / "cpu_best_runtime_by_case.svg",
        "Best CPU runtime by case",
        cpu_best,
        "case",
        "best_runtime_s",
        "family",
        ylabel="Best runtime [s]",
        log=True
    )

if not cuda_solver.empty:
    solver_name_col = cuda_solver.columns[0]
    write_bar_svg(
        FIGS / "cuda_median_runtime_by_pressure_solver.svg",
        "CUDA median runtime by pressure solver",
        cuda_solver[solver_name_col].astype(str).tolist(),
        cuda_solver["median"].tolist(),
        ylabel="Median runtime [s]",
        log=False
    )

if not combined_best.empty:
    write_line_svg(
        FIGS / "combined_best_runtime_by_case_backend.svg",
        "Best runtime by backend and case",
        combined_best,
        "case",
        "best_runtime_s",
        "backend",
        ylabel="Best runtime [s]",
        log=True
    )

(FINAL / "README_PLOTS_AND_COMPARISONS.md").write_text(
"""# Final Plots and Comparisons

This folder contains final comparison CSV tables and SVG figures.

## Main Tables

- `comparisons/cpu_completeness_status.csv`
- `comparisons/cpu_success_failed_overview.csv`
- `comparisons/cpu_successful_runtime_rows.csv`
- `comparisons/cpu_best_runtime_by_case.csv`
- `comparisons/cuda_full_rbgs_rbsor_rows.csv`
- `comparisons/cuda_runtime_by_pressure_solver.csv`
- `comparisons/cuda_best_runtime_by_case.csv`
- `comparisons/combined_best_runtime_by_case_backend.csv`

## Main Figures

- `figures/cpu_success_failed_overview.svg`
- `figures/cpu_best_runtime_by_case.svg`
- `figures/cuda_median_runtime_by_pressure_solver.svg`
- `figures/combined_best_runtime_by_case_backend.svg`

## Notes

Runtime comparisons use successful rows only.
MPI and hybrid case 13 were salvaged from successful rows.
Failed/time-limited rows are reported separately in the completeness tables.
CUDA validation is reported separately from runtime.
"""
)

print("DONE")
print("Tables:", TABLES)
print("Figures:", FIGS)
print("Summary:", FINAL / "README_PLOTS_AND_COMPARISONS.md")
