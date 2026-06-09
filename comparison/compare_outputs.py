#!/usr/bin/env python3
"""
Compare same-setup lid-driven cavity outputs across implementations.

Default use after running all serial solvers:

    python3 compare_outputs.py \
        --matlab-data matlab/results/data \
        --matlab-summary study_summary_quick_matlab.csv \
        --cpp-data cpp/serial/results/data \
        --cpp-summary study_summary_quick.csv \
        --c-data c/serial/results/data \
        --c-summary study_summary_quick.csv \
        --python-data python/serial/results/data \
        --python-summary study_summary_quick.csv \
        --out comparison/results

The script matches cases by physical/numerical setup, not by CaseID:
    N, Re, Scheme, PressureSolver

MATLAB normally has two reference implementations (vectorized and loop). C and
Python now also provide vectorized/looped serial baselines, while C++ remains a
serial baseline. Every non-reference case is compared against every matching
reference implementation.
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd


CASE_RE = re.compile(
    r"case_(?P<id>\d+)_N(?P<N>\d+)_Re(?P<Re>\d+)_(?P<scheme>[A-Za-z0-9]+)_(?P<pressure>[A-Za-z0-9]+)_(?P<implementation>[A-Za-z0-9_]+)_(?P<kind>fields|history)$"
)


@dataclass(frozen=True)
class CaseKey:
    N: int
    Re: int
    scheme: str
    pressure: str
    implementation: str

    @property
    def setup_key(self) -> Tuple[int, int, str, str]:
        return (self.N, self.Re, self.scheme.lower(), self.pressure.upper())


@dataclass(frozen=True)
class DataSource:
    label: str
    data_dir: Path
    summary_name: Optional[str] = None


def latest_summary(data_dir: Path, preferred: Optional[str] = None) -> Path:
    if preferred:
        path = data_dir / preferred
        if path.exists():
            return path
        raise FileNotFoundError(f"Requested summary file was not found: {path}")

    candidates = sorted(data_dir.glob("study_summary*.csv"))
    if not candidates:
        raise FileNotFoundError(f"No study_summary*.csv files found in {data_dir}")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def parse_case_csv(path: Path) -> Optional[CaseKey]:
    match = CASE_RE.search(path.stem)
    if not match:
        return None
    g = match.groupdict()
    return CaseKey(
        N=int(g["N"]),
        Re=int(g["Re"]),
        scheme=g["scheme"].lower(),
        pressure=g["pressure"].upper(),
        implementation=g["implementation"].lower(),
    )


def index_field_files(data_dir: Path) -> Dict[CaseKey, Path]:
    out: Dict[CaseKey, Path] = {}
    for path in data_dir.glob("case_*_fields.csv"):
        key = parse_case_csv(path)
        if key is not None:
            out[key] = path
    return out


def load_grid(path: Path) -> Dict[str, np.ndarray]:
    df = pd.read_csv(path)
    required = {"i", "j", "x", "y", "u", "v", "p", "speed", "vorticity"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")

    grids: Dict[str, np.ndarray] = {}
    for col in ["u", "v", "p", "speed", "vorticity"]:
        grids[col] = (
            df.pivot(index="i", columns="j", values=col)
            .sort_index(axis=0)
            .sort_index(axis=1)
            .to_numpy(dtype=float)
        )
    return grids


def centerline_l2(a: np.ndarray, b: np.ndarray, direction: str) -> float:
    if a.shape != b.shape:
        return math.nan
    n = a.shape[0]
    # MATLAB round((N+1)/2)-1, avoiding Python banker's rounding.
    mid = int(math.floor((n + 1) / 2.0 + 0.5)) - 1
    if direction == "vertical":
        diff = a[:, mid] - b[:, mid]
    else:
        diff = a[mid, :] - b[mid, :]
    return float(np.sqrt(np.mean(diff * diff)))


def compare_fields(reference_field: Path, candidate_field: Path) -> Dict[str, float]:
    ref = load_grid(reference_field)
    cand = load_grid(candidate_field)
    out: Dict[str, float] = {}

    if ref["u"].shape != cand["u"].shape:
        out["field_shape_match"] = 0.0
        for name in [
            "u_Linf", "v_Linf", "speed_Linf", "vorticity_Linf", "p_centered_Linf",
            "u_centerline_L2", "v_centerline_L2",
        ]:
            out[name] = math.nan
        return out

    out["field_shape_match"] = 1.0
    out["u_Linf"] = float(np.max(np.abs(ref["u"] - cand["u"])))
    out["v_Linf"] = float(np.max(np.abs(ref["v"] - cand["v"])))
    out["speed_Linf"] = float(np.max(np.abs(ref["speed"] - cand["speed"])))
    out["vorticity_Linf"] = float(np.max(np.abs(ref["vorticity"] - cand["vorticity"])))

    # Pressure has an arbitrary constant. Compare centered pressures.
    rp = ref["p"] - np.mean(ref["p"])
    cp = cand["p"] - np.mean(cand["p"])
    out["p_centered_Linf"] = float(np.max(np.abs(rp - cp)))

    out["u_centerline_L2"] = centerline_l2(ref["u"], cand["u"], "vertical")
    out["v_centerline_L2"] = centerline_l2(ref["v"], cand["v"], "horizontal")
    return out


def normalize_summary(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "FinalRc" in df.columns and "FinalRcMass" not in df.columns:
        df = df.rename(columns={"FinalRc": "FinalRcMass"})
    for col in ["Scheme", "PressureSolver", "Implementation", "Status", "Quality"]:
        if col in df.columns:
            df[col] = df[col].astype(str)
    return df


def as_float(row: pd.Series, col: str) -> float:
    try:
        return float(row[col])
    except Exception:
        return math.nan


def load_source(source: DataSource) -> Tuple[pd.DataFrame, Dict[CaseKey, Path], Path]:
    summary_file = latest_summary(source.data_dir, source.summary_name)
    summary = normalize_summary(pd.read_csv(summary_file))
    fields = index_field_files(source.data_dir)
    return summary, fields, summary_file


def comparison_rows(reference: DataSource, candidates: List[DataSource]) -> Tuple[List[Dict[str, object]], Path, Dict[str, Path]]:
    rows: List[Dict[str, object]] = []
    ref_summary, ref_fields, ref_summary_file = load_source(reference)
    candidate_summary_files: Dict[str, Path] = {}

    for cand_source in candidates:
        cand_summary, cand_fields, cand_summary_file = load_source(cand_source)
        candidate_summary_files[cand_source.label] = cand_summary_file

        for _, c in cand_summary.iterrows():
            setup = (
                int(c["N"]),
                int(c["Re"]),
                str(c["Scheme"]).lower(),
                str(c["PressureSolver"]).upper(),
            )
            matching_ref = ref_summary[
                (ref_summary["N"].astype(int) == setup[0])
                & (ref_summary["Re"].astype(int) == setup[1])
                & (ref_summary["Scheme"].str.lower() == setup[2])
                & (ref_summary["PressureSolver"].str.upper() == setup[3])
            ]

            cand_impl = str(c["Implementation"]).lower()
            cand_key = CaseKey(setup[0], setup[1], setup[2], setup[3], cand_impl)
            cand_field = cand_fields.get(cand_key)

            for _, r in matching_ref.iterrows():
                ref_impl = str(r["Implementation"]).lower()
                ref_key = CaseKey(setup[0], setup[1], setup[2], setup[3], ref_impl)
                ref_field = ref_fields.get(ref_key)

                ref_runtime = as_float(r, "Runtime_s")
                cand_runtime = as_float(c, "Runtime_s")
                row: Dict[str, object] = {
                    "N": setup[0],
                    "Re": setup[1],
                    "Scheme": setup[2],
                    "PressureSolver": setup[3],
                    "ReferenceSource": reference.label,
                    "ReferenceImplementation": ref_impl,
                    "CandidateSource": cand_source.label,
                    "CandidateImplementation": cand_impl,
                    "ReferenceStatus": r.get("Status", ""),
                    "CandidateStatus": c.get("Status", ""),
                    "ReferenceQuality": r.get("Quality", ""),
                    "CandidateQuality": c.get("Quality", ""),
                    "ReferenceIterations": as_float(r, "Iterations"),
                    "CandidateIterations": as_float(c, "Iterations"),
                    "ReferenceRuntime_s": ref_runtime,
                    "CandidateRuntime_s": cand_runtime,
                    "Runtime_Ratio_Reference_over_Candidate": ref_runtime / cand_runtime if cand_runtime > 0 else math.nan,
                    "ReferenceFinalRcMass": as_float(r, "FinalRcMass"),
                    "CandidateFinalRcMass": as_float(c, "FinalRcMass"),
                    "ReferenceFinalRcDiv": as_float(r, "FinalRcDiv"),
                    "CandidateFinalRcDiv": as_float(c, "FinalRcDiv"),
                    "ReferenceGhia_u_L2": as_float(r, "Ghia_u_L2"),
                    "CandidateGhia_u_L2": as_float(c, "Ghia_u_L2"),
                    "ReferenceGhia_v_L2": as_float(r, "Ghia_v_L2"),
                    "CandidateGhia_v_L2": as_float(c, "Ghia_v_L2"),
                    "Ghia_u_L2_abs_diff": abs(as_float(r, "Ghia_u_L2") - as_float(c, "Ghia_u_L2")),
                    "Ghia_v_L2_abs_diff": abs(as_float(r, "Ghia_v_L2") - as_float(c, "Ghia_v_L2")),
                    "ReferenceFieldCSV": str(ref_field) if ref_field else "",
                    "CandidateFieldCSV": str(cand_field) if cand_field else "",
                }

                # Backward-friendly aliases for the original MATLAB/C++ comparison.
                if reference.label.lower() == "matlab":
                    row["MATLAB_Implementation"] = ref_impl
                    row["MATLAB_Runtime_s"] = ref_runtime
                    row["MATLAB_Status"] = r.get("Status", "")
                    row["MATLAB_Quality"] = r.get("Quality", "")
                if cand_source.label.lower() == "c++":
                    row["CPP_Implementation"] = cand_impl
                    row["CPP_Runtime_s"] = cand_runtime
                    row["CPP_Status"] = c.get("Status", "")
                    row["CPP_Quality"] = c.get("Quality", "")
                    row["Runtime_Ratio_MATLAB_over_CPP"] = ref_runtime / cand_runtime if cand_runtime > 0 else math.nan

                if ref_field and cand_field:
                    try:
                        row.update(compare_fields(ref_field, cand_field))
                    except Exception as exc:
                        row["field_compare_error"] = str(exc)
                else:
                    row["field_shape_match"] = math.nan
                    for name in ["u_Linf", "v_Linf", "speed_Linf", "vorticity_Linf", "p_centered_Linf", "u_centerline_L2", "v_centerline_L2"]:
                        row[name] = math.nan

                rows.append(row)

    return rows, ref_summary_file, candidate_summary_files


def write_report(df: pd.DataFrame, out_dir: Path, reference: DataSource, ref_summary_file: Path, candidate_summary_files: Dict[str, Path]) -> Path:
    report = out_dir / "comparison_report.md"

    if df.empty:
        text = "# Serial Solver Same-Setup Comparison Report\n\nNo matching cases were found.\n"
        report.write_text(text, encoding="utf-8")
        return report

    def worst(col: str) -> float:
        return float(df[col].dropna().max()) if col in df and df[col].notna().any() else math.nan

    lines: List[str] = []
    lines.append("# Serial Solver Same-Setup Comparison Report\n\n")
    lines.append(f"Reference source: **{reference.label}**\n\n")
    lines.append(f"Reference summary: `{ref_summary_file}`\n\n")
    lines.append("Candidate summaries:\n")
    for label, path in candidate_summary_files.items():
        lines.append(f"- **{label}**: `{path}`\n")
    lines.append(f"\nCompared rows: **{len(df)}**\n")
    lines.append("\n## Compared implementations\n\n")
    impl_counts = df.groupby(["ReferenceImplementation", "CandidateSource", "CandidateImplementation"]).size().reset_index(name="ComparedRows")
    lines.append(impl_counts.to_markdown(index=False))
    lines.append("\n\n## Main field differences\n")
    lines.append("These values compare each candidate field directly against the reference field on the same grid. Pressure is compared after subtracting the mean because pressure has an arbitrary constant offset.\n")
    for col in ["u_Linf", "v_Linf", "speed_Linf", "vorticity_Linf", "p_centered_Linf", "u_centerline_L2", "v_centerline_L2"]:
        lines.append(f"- Worst `{col}`: `{worst(col):.6e}`\n")
    lines.append("\n## Ghia validation metric differences\n")
    lines.append(f"- Worst absolute difference in `Ghia_u_L2`: `{worst('Ghia_u_L2_abs_diff'):.6e}`\n")
    lines.append(f"- Worst absolute difference in `Ghia_v_L2`: `{worst('Ghia_v_L2_abs_diff'):.6e}`\n")
    lines.append("\n## Runtime ratios\n\n")
    ratio = df.groupby(["ReferenceImplementation", "CandidateSource", "CandidateImplementation"])["Runtime_Ratio_Reference_over_Candidate"].mean().reset_index()
    lines.append(ratio.to_markdown(index=False))
    lines.append("\n\nA ratio larger than 1 means the reference run was slower than the candidate for that setup.\n")
    lines.append("\n## Interpretation\n")
    lines.append("Small non-zero differences are normal because each language follows a slightly different floating-point operation order and array update path. Judge the comparison using field differences, centerline profiles, validation errors, residual behavior, and runtime rather than bit-for-bit equality.\n")
    lines.append("\n## Output files\n")
    lines.append("- `comparison_summary.csv`: full numerical comparison table.\n")
    report.write_text("".join(lines), encoding="utf-8")
    return report


def parse_extra_sources(values: Optional[List[str]]) -> List[DataSource]:
    sources: List[DataSource] = []
    if not values:
        return sources
    for item in values:
        if "=" not in item:
            raise ValueError(f"--candidate expects LABEL=PATH, got: {item}")
        label, path = item.split("=", 1)
        sources.append(DataSource(label.strip(), Path(path.strip())))
    return sources


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare same-setup lid cavity outputs across serial implementations.")
    parser.add_argument("--matlab-data", type=Path, default=Path("matlab/results/data"), help="Reference data directory by default")
    parser.add_argument("--reference-data", type=Path, default=None, help="Override reference data directory")
    parser.add_argument("--reference-label", type=str, default="MATLAB")
    parser.add_argument("--cpp-data", type=Path, default=None)
    parser.add_argument("--c-data", type=Path, default=None)
    parser.add_argument("--python-data", type=Path, default=None)
    parser.add_argument("--candidate", action="append", default=None, help="Extra candidate as LABEL=PATH")
    parser.add_argument("--out", type=Path, default=Path("comparison/results"))
    parser.add_argument("--matlab-summary", type=str, default=None)
    parser.add_argument("--reference-summary", type=str, default=None)
    parser.add_argument("--cpp-summary", type=str, default=None)
    parser.add_argument("--c-summary", type=str, default=None)
    parser.add_argument("--python-summary", type=str, default=None)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    reference_dir = args.reference_data if args.reference_data is not None else args.matlab_data
    reference_summary = args.reference_summary if args.reference_summary is not None else args.matlab_summary
    reference = DataSource(args.reference_label, reference_dir, reference_summary)

    candidates: List[DataSource] = []
    if args.cpp_data is not None:
        candidates.append(DataSource("C++", args.cpp_data, args.cpp_summary))
    if args.c_data is not None:
        candidates.append(DataSource("C", args.c_data, args.c_summary))
    if args.python_data is not None:
        candidates.append(DataSource("Python", args.python_data, args.python_summary))
    candidates.extend(parse_extra_sources(args.candidate))

    if not candidates:
        # Backward-compatible default: original MATLAB vs C++ layout.
        default_cpp = Path("cpp/serial/results/data")
        if default_cpp.exists():
            candidates.append(DataSource("C++", default_cpp, args.cpp_summary))
        else:
            raise FileNotFoundError("No candidate data supplied. Use --cpp-data, --c-data, --python-data, or --candidate LABEL=PATH.")

    rows, ref_summary_file, candidate_summary_files = comparison_rows(reference, candidates)
    df = pd.DataFrame(rows)

    out_csv = args.out / "comparison_summary.csv"
    df.to_csv(out_csv, index=False)
    report = write_report(df, args.out, reference, ref_summary_file, candidate_summary_files)

    print(f"Reference summary: {ref_summary_file}")
    for label, path in candidate_summary_files.items():
        print(f"{label} summary:      {path}")
    print(f"Wrote:             {out_csv}")
    print(f"Wrote:             {report}")
    if not df.empty:
        cols = [
            "N", "Re", "Scheme", "PressureSolver", "ReferenceImplementation", "CandidateSource", "CandidateImplementation",
            "u_Linf", "v_Linf", "u_centerline_L2", "v_centerline_L2", "Runtime_Ratio_Reference_over_Candidate",
        ]
        existing = [c for c in cols if c in df.columns]
        print("\nPreview:")
        print(df[existing].head(16).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
