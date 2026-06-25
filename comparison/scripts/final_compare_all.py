#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
import warnings

import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
SPLIT_DIR = ROOT / "comparison" / "results" / "split"
RAW_DIR = ROOT / "comparison" / "results" / "raw"
PY_MPI_DIR = ROOT / "python" / "mpi" / "results" / "data"
OUT_DIR = ROOT / "comparison" / "results" / "final"
FIG_DIR = ROOT / "comparison" / "figures" / "final"

OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_ROWS = {
    "c_serial": 36,
    "cpp_serial": 36,
    "c_openmp": 36,
    "cpp_openmp": 36,
    "python_vectorized": 36,
    "python_looped": 36,
    "octave_vectorized": 36,
    "octave_looped": 36,
    "c_mpi": 36,
    "cpp_mpi": 36,
    "python_mpi": 72,
}


def clean_col(c: str) -> str:
    return str(c).strip().replace(" ", "_").replace("-", "_")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [clean_col(c) for c in df.columns]
    return df


def detect_col(df: pd.DataFrame, patterns: list[str], numeric: bool = False) -> str | None:
    cols = list(df.columns)
    lowered = {c: c.lower() for c in cols}

    for pat in patterns:
        for c in cols:
            if re.search(pat, lowered[c]):
                if numeric:
                    s = pd.to_numeric(df[c], errors="coerce")
                    if s.notna().sum() > 0:
                        return c
                else:
                    return c
    return None


def numericify(df: pd.DataFrame, col: str | None):
    if col and col in df.columns:
        return pd.to_numeric(df[col], errors="coerce")
    return pd.Series([float("nan")] * len(df), index=df.index)


def solver_from_split_filename(path: Path) -> str:
    name = path.name
    m = re.match(r"(.+?)_case_0*\d+\.csv$", name)
    if m:
        return m.group(1)
    m = re.match(r"(.+?)_.*\.csv$", name)
    if m:
        return m.group(1)
    return path.stem


def read_one_csv(path: Path, solver_group: str, source_type: str) -> pd.DataFrame | None:
    try:
        df = pd.read_csv(path)
    except Exception as e:
        print(f"[WARN] Could not read {path}: {e}")
        return None

    if df.empty:
        print(f"[WARN] Empty dataframe: {path}")
        return None

    df = normalize_columns(df)
    df["solver_group"] = solver_group
    df["source_type"] = source_type
    df["source_file"] = str(path.relative_to(ROOT))

    return df


def collect_results() -> pd.DataFrame:
    frames = []

    # Array split results
    if SPLIT_DIR.exists():
        for path in sorted(SPLIT_DIR.glob("*.csv")):
            solver = solver_from_split_filename(path)
            df = read_one_csv(path, solver, "array_split")
            if df is not None:
                frames.append(df)

    # Raw MPI full summaries
    raw_map = {
        "c_mpi_r8_full.csv": "c_mpi",
        "cpp_mpi_r8_full.csv": "cpp_mpi",
        "python_mpi_r8_full.csv": "python_mpi",
    }

    if RAW_DIR.exists():
        for fname, solver in raw_map.items():
            path = RAW_DIR / fname
            if path.exists():
                df = read_one_csv(path, solver, "raw_mpi")
                if df is not None:
                    frames.append(df)

    # Python MPI parts, if no merged file exists or if we want partial visibility
    if PY_MPI_DIR.exists():
        for path in sorted(PY_MPI_DIR.glob("study_summary_mpi_part_*.csv")):
            if "rank" in path.name:
                continue
            df = read_one_csv(path, "python_mpi", "python_mpi_part")
            if df is not None:
                frames.append(df)

    if not frames:
        raise SystemExit("No CSV result files found.")

    # Different files may have different columns
    all_df = pd.concat(frames, ignore_index=True, sort=False)

    return all_df


def add_standard_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    n_col = detect_col(df, [r"^n$", r"mesh", r"grid", r"nx"], numeric=True)
    re_col = detect_col(df, [r"^re$", r"reynolds"], numeric=True)
    scheme_col = detect_col(df, [r"scheme"], numeric=False)
    pressure_col = detect_col(df, [r"pressure"], numeric=False)
    impl_col = detect_col(df, [r"implementation", r"impl"], numeric=False)
    case_col = detect_col(df, [r"case"], numeric=True)

    runtime_col = detect_col(
        df,
        [
            r"runtime.*s",
            r"time.*s",
            r"elapsed.*s",
            r"wall.*s",
            r"runtime",
            r"elapsed",
            r"wall",
            r"cpu",
        ],
        numeric=True,
    )

    validation_col = detect_col(
        df,
        [
            r"ghia.*error",
            r"validation.*error",
            r"error.*ghia",
            r"l2.*error",
            r"max.*error",
            r"mean.*error",
        ],
        numeric=True,
    )

    residual_col = detect_col(
        df,
        [
            r"residual",
            r"continuity",
            r"divergence",
        ],
        numeric=True,
    )

    iterations_col = detect_col(
        df,
        [
            r"iterations$",
            r"iter$",
            r"niter",
        ],
        numeric=True,
    )

    quality_col = detect_col(df, [r"quality", r"status", r"validation"], numeric=False)

    df["case_id_std"] = numericify(df, case_col)
    df["N_std"] = numericify(df, n_col)
    df["Re_std"] = numericify(df, re_col)
    df["runtime_std"] = numericify(df, runtime_col)
    df["validation_error_std"] = numericify(df, validation_col)
    df["residual_std"] = numericify(df, residual_col)
    df["iterations_std"] = numericify(df, iterations_col)

    df["scheme_std"] = df[scheme_col].astype(str) if scheme_col else ""
    df["pressure_std"] = df[pressure_col].astype(str) if pressure_col else ""
    df["implementation_std"] = df[impl_col].astype(str) if impl_col else df["solver_group"].astype(str)
    df["quality_std"] = df[quality_col].astype(str) if quality_col else ""

    print()
    print("Detected columns:")
    print(f"N column:                 {n_col}")
    print(f"Re column:                {re_col}")
    print(f"case column:              {case_col}")
    print(f"scheme column:            {scheme_col}")
    print(f"pressure column:          {pressure_col}")
    print(f"implementation column:    {impl_col}")
    print(f"runtime column:           {runtime_col}")
    print(f"validation error column:  {validation_col}")
    print(f"residual column:          {residual_col}")
    print(f"iterations column:        {iterations_col}")
    print(f"quality/status column:    {quality_col}")
    print()

    return df


def completeness_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for solver, expected in EXPECTED_ROWS.items():
        sub = df[df["solver_group"] == solver]
        count = len(sub)

        if "case_id_std" in sub.columns and sub["case_id_std"].notna().any():
            case_ids = sorted(set(int(x) for x in sub["case_id_std"].dropna()))
        else:
            case_ids = []

        if solver == "python_mpi":
            expected_ids = set(range(1, expected + 1))
        else:
            expected_ids = set(range(1, expected + 1))

        missing = sorted(expected_ids - set(case_ids)) if case_ids else []

        rows.append(
            {
                "solver_group": solver,
                "rows_found": count,
                "expected_rows": expected,
                "complete": count >= expected and len(missing) == 0,
                "missing_case_ids": " ".join(map(str, missing)) if missing else "none",
            }
        )

    return pd.DataFrame(rows)


def runtime_summary(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df["runtime_std"].notna()].copy()

    if valid.empty:
        return pd.DataFrame()

    summary = (
        valid.groupby("solver_group")
        .agg(
            rows=("runtime_std", "count"),
            total_runtime=("runtime_std", "sum"),
            mean_runtime=("runtime_std", "mean"),
            median_runtime=("runtime_std", "median"),
            min_runtime=("runtime_std", "min"),
            max_runtime=("runtime_std", "max"),
        )
        .reset_index()
        .sort_values("median_runtime")
    )

    return summary


def validation_summary(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df["validation_error_std"].notna()].copy()

    if valid.empty:
        return pd.DataFrame()

    summary = (
        valid.groupby("solver_group")
        .agg(
            rows=("validation_error_std", "count"),
            mean_validation_error=("validation_error_std", "mean"),
            median_validation_error=("validation_error_std", "median"),
            min_validation_error=("validation_error_std", "min"),
            max_validation_error=("validation_error_std", "max"),
        )
        .reset_index()
        .sort_values("median_validation_error")
    )

    return summary


def runtime_by_case(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "solver_group",
        "case_id_std",
        "N_std",
        "Re_std",
        "scheme_std",
        "pressure_std",
        "implementation_std",
        "runtime_std",
        "validation_error_std",
        "residual_std",
        "iterations_std",
        "quality_std",
        "source_file",
    ]

    cols = [c for c in cols if c in df.columns]
    out = df[cols].copy()

    sort_cols = [c for c in ["N_std", "Re_std", "scheme_std", "pressure_std", "solver_group"] if c in out.columns]
    if sort_cols:
        out = out.sort_values(sort_cols)

    return out


def plot_runtime_box(df: pd.DataFrame):
    valid = df[df["runtime_std"].notna()].copy()
    if valid.empty:
        print("[WARN] No runtime data to plot.")
        return

    groups = [
        g for g, sub in valid.groupby("solver_group")
        if sub["runtime_std"].notna().sum() > 0
    ]

    data = [valid.loc[valid["solver_group"] == g, "runtime_std"].dropna() for g in groups]

    plt.figure(figsize=(14, 7))
    plt.boxplot(data, labels=groups, showfliers=False)
    plt.yscale("log")
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Runtime / time column, log scale")
    plt.title("Runtime distribution by solver")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "runtime_boxplot_by_solver.png", dpi=200)
    plt.close()


def plot_validation_box(df: pd.DataFrame):
    valid = df[df["validation_error_std"].notna()].copy()
    if valid.empty:
        print("[WARN] No validation error data to plot.")
        return

    groups = [
        g for g, sub in valid.groupby("solver_group")
        if sub["validation_error_std"].notna().sum() > 0
    ]

    data = [valid.loc[valid["solver_group"] == g, "validation_error_std"].dropna() for g in groups]

    plt.figure(figsize=(14, 7))
    plt.boxplot(data, labels=groups, showfliers=False)
    plt.yscale("log")
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Validation error, log scale")
    plt.title("Validation error distribution by solver")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "validation_error_boxplot_by_solver.png", dpi=200)
    plt.close()


def plot_runtime_bar(summary: pd.DataFrame):
    if summary.empty:
        return

    plt.figure(figsize=(14, 7))
    plt.bar(summary["solver_group"], summary["median_runtime"])
    plt.yscale("log")
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Median runtime / time column, log scale")
    plt.title("Median runtime by solver")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "median_runtime_by_solver.png", dpi=200)
    plt.close()


def plot_validation_bar(summary: pd.DataFrame):
    if summary.empty:
        return

    plt.figure(figsize=(14, 7))
    plt.bar(summary["solver_group"], summary["median_validation_error"])
    plt.yscale("log")
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Median validation error, log scale")
    plt.title("Median validation error by solver")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "median_validation_error_by_solver.png", dpi=200)
    plt.close()


def main():
    warnings.filterwarnings("ignore", category=UserWarning)

    df = collect_results()
    df = add_standard_columns(df)

    all_out = OUT_DIR / "all_results_collected.csv"
    df.to_csv(all_out, index=False)

    complete = completeness_summary(df)
    complete.to_csv(OUT_DIR / "completeness_summary.csv", index=False)

    rt = runtime_summary(df)
    rt.to_csv(OUT_DIR / "runtime_summary_by_solver.csv", index=False)

    val = validation_summary(df)
    val.to_csv(OUT_DIR / "validation_summary_by_solver.csv", index=False)

    by_case = runtime_by_case(df)
    by_case.to_csv(OUT_DIR / "runtime_validation_by_case.csv", index=False)

    plot_runtime_box(df)
    plot_validation_box(df)
    plot_runtime_bar(rt)
    plot_validation_bar(val)

    print("==================================================")
    print("COMPLETENESS SUMMARY")
    print("==================================================")
    print(complete.to_string(index=False))

    print()
    print("==================================================")
    print("RUNTIME SUMMARY BY SOLVER")
    print("==================================================")
    if rt.empty:
        print("No runtime column detected.")
    else:
        print(rt.to_string(index=False))

    print()
    print("==================================================")
    print("VALIDATION SUMMARY BY SOLVER")
    print("==================================================")
    if val.empty:
        print("No validation error column detected.")
    else:
        print(val.to_string(index=False))

    print()
    print("==================================================")
    print("OUTPUT FILES")
    print("==================================================")
    print(f"{all_out}")
    print(f"{OUT_DIR / 'completeness_summary.csv'}")
    print(f"{OUT_DIR / 'runtime_summary_by_solver.csv'}")
    print(f"{OUT_DIR / 'validation_summary_by_solver.csv'}")
    print(f"{OUT_DIR / 'runtime_validation_by_case.csv'}")
    print(f"{FIG_DIR / 'runtime_boxplot_by_solver.png'}")
    print(f"{FIG_DIR / 'validation_error_boxplot_by_solver.png'}")
    print(f"{FIG_DIR / 'median_runtime_by_solver.png'}")
    print(f"{FIG_DIR / 'median_validation_error_by_solver.png'}")


if __name__ == "__main__":
    main()
