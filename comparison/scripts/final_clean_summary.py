#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
INFILE = ROOT / "comparison/results/final/all_results_collected.csv"
OUT = ROOT / "comparison/results/final_clean"
FIG = ROOT / "comparison/figures/final_clean"

OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INFILE)

# Keep the real solver names used in the runtime table.
expected = {
    "c_serial": 36,
    "cpp_serial": 36,
    "c_openmp_t4": 36,
    "cpp_openmp_t4": 36,
    "python_vectorized": 36,
    "python_looped": 36,
    "octave_vectorized": 36,
    "octave_looped": 36,
    "c_mpi": 36,
    "cpp_mpi": 36,
    "python_mpi": 72,
}

# Detect standard columns.
case_col = "CaseID" if "CaseID" in df.columns else None
runtime_col = "Runtime_s" if "Runtime_s" in df.columns else None
residual_col = "AvgPoissonRelResidual" if "AvgPoissonRelResidual" in df.columns else None
quality_col = "Quality" if "Quality" in df.columns else None

# --------------------------------------------------
# Completeness
# --------------------------------------------------
rows = []
for solver, exp in expected.items():
    sub = df[df["solver_group"] == solver].copy()
    found_rows = len(sub)

    if case_col and found_rows:
        found_ids = sorted(set(pd.to_numeric(sub[case_col], errors="coerce").dropna().astype(int)))
        missing = sorted(set(range(1, exp + 1)) - set(found_ids))
    else:
        found_ids = []
        missing = list(range(1, exp + 1)) if found_rows == 0 else []

    rows.append({
        "solver_group": solver,
        "rows_found": found_rows,
        "expected_rows": exp,
        "complete": found_rows >= exp and len(missing) == 0,
        "missing_case_ids": " ".join(map(str, missing)) if missing else "none",
    })

complete = pd.DataFrame(rows)
complete.to_csv(OUT / "completeness_summary_fixed.csv", index=False)

# --------------------------------------------------
# Runtime summary
# --------------------------------------------------
if runtime_col:
    df[runtime_col] = pd.to_numeric(df[runtime_col], errors="coerce")
    runtime = (
        df.dropna(subset=[runtime_col])
        .groupby("solver_group")
        .agg(
            rows=(runtime_col, "count"),
            total_runtime_s=(runtime_col, "sum"),
            mean_runtime_s=(runtime_col, "mean"),
            median_runtime_s=(runtime_col, "median"),
            min_runtime_s=(runtime_col, "min"),
            max_runtime_s=(runtime_col, "max"),
        )
        .reset_index()
        .sort_values("median_runtime_s")
    )
else:
    runtime = pd.DataFrame()

runtime.to_csv(OUT / "runtime_summary_fixed.csv", index=False)

# --------------------------------------------------
# Residual / convergence summary
# --------------------------------------------------
if residual_col:
    df[residual_col] = pd.to_numeric(df[residual_col], errors="coerce")
    residual = (
        df.dropna(subset=[residual_col])
        .groupby("solver_group")
        .agg(
            rows=(residual_col, "count"),
            mean_avg_poisson_rel_residual=(residual_col, "mean"),
            median_avg_poisson_rel_residual=(residual_col, "median"),
            min_avg_poisson_rel_residual=(residual_col, "min"),
            max_avg_poisson_rel_residual=(residual_col, "max"),
        )
        .reset_index()
        .sort_values("median_avg_poisson_rel_residual")
    )
else:
    residual = pd.DataFrame()

residual.to_csv(OUT / "residual_summary_by_solver.csv", index=False)

# --------------------------------------------------
# Quality / validation category summary
# --------------------------------------------------
if quality_col:
    quality = (
        df.groupby(["solver_group", quality_col])
        .size()
        .reset_index(name="count")
        .sort_values(["solver_group", quality_col])
    )

    quality_pivot = (
        quality.pivot(index="solver_group", columns=quality_col, values="count")
        .fillna(0)
        .astype(int)
        .reset_index()
    )
else:
    quality = pd.DataFrame()
    quality_pivot = pd.DataFrame()

quality.to_csv(OUT / "quality_counts_long.csv", index=False)
quality_pivot.to_csv(OUT / "quality_counts_by_solver.csv", index=False)

# --------------------------------------------------
# Keep a clean by-case table
# --------------------------------------------------
keep_cols = [
    "solver_group",
    "CaseID",
    "Implementation",
    "N",
    "Re",
    "Scheme",
    "PressureSolver",
    "Runtime_s",
    "Iterations",
    "AvgPoissonRelResidual",
    "Quality",
    "source_file",
]
keep_cols = [c for c in keep_cols if c in df.columns]
by_case = df[keep_cols].copy()
by_case.to_csv(OUT / "runtime_residual_quality_by_case.csv", index=False)

# --------------------------------------------------
# Plots
# --------------------------------------------------
if not runtime.empty:
    plt.figure(figsize=(13, 7))
    plt.bar(runtime["solver_group"], runtime["median_runtime_s"])
    plt.yscale("log")
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Median runtime [s], log scale")
    plt.title("Median runtime by solver")
    plt.tight_layout()
    plt.savefig(FIG / "median_runtime_by_solver_fixed.png", dpi=200)
    plt.close()

if not residual.empty:
    plt.figure(figsize=(13, 7))
    plt.bar(residual["solver_group"], residual["median_avg_poisson_rel_residual"])
    plt.yscale("log")
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Median AvgPoissonRelResidual, log scale")
    plt.title("Convergence residual by solver")
    plt.tight_layout()
    plt.savefig(FIG / "median_residual_by_solver.png", dpi=200)
    plt.close()

if not quality_pivot.empty:
    qp = quality_pivot.set_index("solver_group")
    qp.plot(kind="bar", stacked=True, figsize=(13, 7))
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Case count")
    plt.title("Validation / quality categories by solver")
    plt.tight_layout()
    plt.savefig(FIG / "quality_counts_by_solver.png", dpi=200)
    plt.close()

print()
print("===== FIXED COMPLETENESS =====")
print(complete.to_string(index=False))

print()
print("===== FIXED RUNTIME SUMMARY =====")
print(runtime.to_string(index=False) if not runtime.empty else "No runtime column found.")

print()
print("===== RESIDUAL / CONVERGENCE SUMMARY =====")
print(residual.to_string(index=False) if not residual.empty else "No residual column found.")

print()
print("===== QUALITY / VALIDATION CATEGORY SUMMARY =====")
print(quality_pivot.to_string(index=False) if not quality_pivot.empty else "No quality column found.")

print()
print("Created:")
for p in sorted(OUT.glob("*.csv")):
    print(p)
for p in sorted(FIG.glob("*.png")):
    print(p)
