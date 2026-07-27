#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "comparison/results/final_clean"
FIG = ROOT / "comparison/figures/report_pngs"
FIG.mkdir(parents=True, exist_ok=True)

runtime_file = DATA / "runtime_summary_fixed.csv"
residual_file = DATA / "residual_summary_by_solver.csv"
quality_file = DATA / "quality_counts_by_solver.csv"
complete_file = DATA / "completeness_summary_fixed.csv"
by_case_file = DATA / "runtime_residual_quality_by_case.csv"

runtime = pd.read_csv(runtime_file)
residual = pd.read_csv(residual_file)
quality = pd.read_csv(quality_file)
complete = pd.read_csv(complete_file)
by_case = pd.read_csv(by_case_file)

complete_solvers = set(complete.loc[complete["complete"] == True, "solver_group"])

def save_bar(df, x, y, title, ylabel, outfile, log=True):
    d = df.copy()
    plt.figure(figsize=(13, 7))
    plt.bar(d[x].astype(str), d[y])
    if log:
        plt.yscale("log")
    plt.xticks(rotation=45, ha="right")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(FIG / outfile, dpi=220)
    plt.close()

# 1) Runtime all solvers
save_bar(
    runtime.sort_values("median_runtime_s"),
    "solver_group",
    "median_runtime_s",
    "Median runtime by solver",
    "Median runtime [s], log scale",
    "01_median_runtime_all_solvers.png",
)

# 2) Runtime complete solvers only
runtime_complete = runtime[runtime["solver_group"].isin(complete_solvers)].sort_values("median_runtime_s")
save_bar(
    runtime_complete,
    "solver_group",
    "median_runtime_s",
    "Median runtime by solver, complete solvers only",
    "Median runtime [s], log scale",
    "02_median_runtime_complete_solvers_only.png",
)

# 3) Mean runtime complete solvers only
save_bar(
    runtime_complete.sort_values("mean_runtime_s"),
    "solver_group",
    "mean_runtime_s",
    "Mean runtime by solver, complete solvers only",
    "Mean runtime [s], log scale",
    "03_mean_runtime_complete_solvers_only.png",
)

# 4) Total runtime all solvers
save_bar(
    runtime.sort_values("total_runtime_s"),
    "solver_group",
    "total_runtime_s",
    "Total measured runtime by solver",
    "Total runtime [s], log scale",
    "04_total_runtime_all_solvers.png",
)

# 5) Residual all solvers
save_bar(
    residual.sort_values("median_avg_poisson_rel_residual"),
    "solver_group",
    "median_avg_poisson_rel_residual",
    "Median Poisson residual by solver",
    "Median AvgPoissonRelResidual, log scale",
    "05_median_residual_all_solvers.png",
)

# 6) Residual complete solvers only
residual_complete = residual[residual["solver_group"].isin(complete_solvers)].sort_values("median_avg_poisson_rel_residual")
save_bar(
    residual_complete,
    "solver_group",
    "median_avg_poisson_rel_residual",
    "Median Poisson residual, complete solvers only",
    "Median AvgPoissonRelResidual, log scale",
    "06_median_residual_complete_solvers_only.png",
)

# 7) Quality stacked bar
q = quality.copy()
q = q.set_index("solver_group")
plt.figure(figsize=(13, 7))
q.plot(kind="bar", stacked=True, figsize=(13, 7))
plt.xticks(rotation=45, ha="right")
plt.ylabel("Number of cases")
plt.title("Quality categories by solver")
plt.tight_layout()
plt.savefig(FIG / "07_quality_categories_by_solver.png", dpi=220)
plt.close()

# 8) Completeness
c = complete.copy()
c["completion_percent"] = 100.0 * c["rows_found"] / c["expected_rows"]
plt.figure(figsize=(13, 7))
plt.bar(c["solver_group"], c["completion_percent"])
plt.xticks(rotation=45, ha="right")
plt.ylabel("Completed cases [%]")
plt.ylim(0, 105)
plt.title("Completeness by solver")
plt.tight_layout()
plt.savefig(FIG / "08_completeness_by_solver.png", dpi=220)
plt.close()

# 9) Runtime distribution boxplot
valid = by_case.dropna(subset=["Runtime_s"]).copy()
groups = list(runtime.sort_values("median_runtime_s")["solver_group"])
data = [valid.loc[valid["solver_group"] == g, "Runtime_s"].dropna() for g in groups if (valid["solver_group"] == g).any()]
labels = [g for g in groups if (valid["solver_group"] == g).any()]
plt.figure(figsize=(14, 7))
plt.boxplot(data, tick_labels=labels, showfliers=False)
plt.yscale("log")
plt.xticks(rotation=45, ha="right")
plt.ylabel("Runtime [s], log scale")
plt.title("Runtime distribution by solver")
plt.tight_layout()
plt.savefig(FIG / "09_runtime_boxplot_by_solver.png", dpi=220)
plt.close()

# 10) Runtime by grid N, median
if "N" in valid.columns:
    med = valid.groupby(["solver_group", "N"])["Runtime_s"].median().reset_index()
    for solver in med["solver_group"].unique():
        sub = med[med["solver_group"] == solver].sort_values("N")
        plt.plot(sub["N"], sub["Runtime_s"], marker="o", label=solver)
    plt.yscale("log")
    plt.xlabel("Grid size N")
    plt.ylabel("Median runtime [s], log scale")
    plt.title("Runtime scaling with grid size")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(FIG / "10_runtime_vs_grid_size.png", dpi=220)
    plt.close()

# 11) Runtime by Reynolds number
if "Re" in valid.columns:
    med = valid.groupby(["solver_group", "Re"])["Runtime_s"].median().reset_index()
    for solver in med["solver_group"].unique():
        sub = med[med["solver_group"] == solver].sort_values("Re")
        plt.plot(sub["Re"], sub["Runtime_s"], marker="o", label=solver)
    plt.yscale("log")
    plt.xlabel("Reynolds number")
    plt.ylabel("Median runtime [s], log scale")
    plt.title("Runtime versus Reynolds number")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(FIG / "11_runtime_vs_reynolds.png", dpi=220)
    plt.close()

# 12) Speedup vs serial C/C++ using median runtime
r = runtime.set_index("solver_group")
speed_rows = []
if "c_serial" in r.index:
    base = r.loc["c_serial", "median_runtime_s"]
    for solver in ["c_openmp_t4", "c_mpi"]:
        if solver in r.index:
            speed_rows.append({"solver_group": solver, "speedup_vs_c_serial": base / r.loc[solver, "median_runtime_s"]})
if "cpp_serial" in r.index:
    base = r.loc["cpp_serial", "median_runtime_s"]
    for solver in ["cpp_openmp_t4", "cpp_mpi"]:
        if solver in r.index:
            speed_rows.append({"solver_group": solver, "speedup_vs_cpp_serial": base / r.loc[solver, "median_runtime_s"]})

speed = pd.DataFrame(speed_rows)
speed.to_csv(DATA / "speedup_summary.csv", index=False)

if not speed.empty:
    plt.figure(figsize=(10, 6))
    labels = []
    vals = []
    for _, row in speed.iterrows():
        solver = row["solver_group"]
        if "speedup_vs_c_serial" in row and pd.notna(row.get("speedup_vs_c_serial")):
            labels.append(solver + " vs c_serial")
            vals.append(row["speedup_vs_c_serial"])
        if "speedup_vs_cpp_serial" in row and pd.notna(row.get("speedup_vs_cpp_serial")):
            labels.append(solver + " vs cpp_serial")
            vals.append(row["speedup_vs_cpp_serial"])
    plt.bar(labels, vals)
    plt.xticks(rotation=30, ha="right")
    plt.ylabel("Speedup based on median runtime")
    plt.title("Parallel speedup versus serial baseline")
    plt.tight_layout()
    plt.savefig(FIG / "12_speedup_vs_serial.png", dpi=220)
    plt.close()

print("Created PNG report figures:")
for p in sorted(FIG.glob("*.png")):
    print(p)

print()
print("Created speedup table:")
print(DATA / "speedup_summary.csv")
