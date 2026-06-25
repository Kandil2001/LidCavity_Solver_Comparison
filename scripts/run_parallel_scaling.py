#!/usr/bin/env python3
"""Run OpenMP and MPI scaling checks and create scaling CSV/plots.

OpenMP scaling here is strong scaling for one fixed case.
MPI scaling here is case-level scaling for the same benchmark list; it measures
how fast a parameter sweep finishes when distributed over more ranks. This is
not domain-decomposition scaling.

Examples from the repository root:

    python3 scripts/run_parallel_scaling.py --targets c_openmp,cpp_openmp --threads 1,2,4,8
    python3 scripts/run_parallel_scaling.py --targets c_mpi,cpp_mpi,python_mpi --ranks 1,2,4 --mode quick
"""
from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd


@dataclass(frozen=True)
class TargetSpec:
    key: str
    name: str
    method: str
    folder: Path
    build_cmd: Optional[List[str]]
    run_cmd: List[str]
    scaling_csv: Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_int_list(raw: str) -> List[int]:
    values = [int(x.strip()) for x in raw.split(",") if x.strip()]
    if not values:
        raise argparse.ArgumentTypeError("Provide at least one value")
    if any(v < 1 for v in values):
        raise argparse.ArgumentTypeError("Values must be positive integers")
    return sorted(dict.fromkeys(values))


def parse_targets(raw: str) -> List[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]


def target_specs(root: Path, python_exe: str) -> Dict[str, TargetSpec]:
    return {
        "c_openmp": TargetSpec(
            key="c_openmp",
            name="C OpenMP",
            method="OpenMP strong scaling",
            folder=root / "c" / "openmp",
            build_cmd=["make", "build"],
            run_cmd=["./bin/lid_cavity_c_openmp"],
            scaling_csv=root / "c" / "openmp" / "results" / "scaling" / "openmp_scaling.csv",
        ),
        "cpp_openmp": TargetSpec(
            key="cpp_openmp",
            name="C++ OpenMP",
            method="OpenMP strong scaling",
            folder=root / "cpp" / "openmp",
            build_cmd=["make", "build"],
            run_cmd=["./bin/lid_cavity_openmp"],
            scaling_csv=root / "cpp" / "openmp" / "results" / "scaling" / "openmp_scaling.csv",
        ),
        "c_mpi": TargetSpec(
            key="c_mpi",
            name="C MPI case-parallel",
            method="MPI case-level scaling",
            folder=root / "c" / "mpi",
            build_cmd=["make", "build"],
            run_cmd=["make"],
            scaling_csv=root / "c" / "mpi" / "results" / "scaling" / "mpi_scaling.csv",
        ),
        "cpp_mpi": TargetSpec(
            key="cpp_mpi",
            name="C++ MPI case-parallel",
            method="MPI case-level scaling",
            folder=root / "cpp" / "mpi",
            build_cmd=["make", "build"],
            run_cmd=["make"],
            scaling_csv=root / "cpp" / "mpi" / "results" / "scaling" / "mpi_scaling.csv",
        ),
        "python_mpi": TargetSpec(
            key="python_mpi",
            name="Python MPI case-parallel",
            method="MPI case-level scaling",
            folder=root / "python" / "mpi",
            build_cmd=None,
            run_cmd=["make"],
            scaling_csv=root / "python" / "mpi" / "results" / "scaling" / "mpi_scaling.csv",
        ),
    }


def run_timed(cmd: List[str], cwd: Path, env: Optional[Dict[str, str]] = None) -> Tuple[float, int]:
    printable = " ".join(cmd)
    print(f"$ (cd {cwd} && {printable})", flush=True)
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    start = time.perf_counter()
    proc = subprocess.run(cmd, cwd=cwd, env=merged_env)
    elapsed = time.perf_counter() - start
    return elapsed, proc.returncode


def write_target_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "Solver", "Target", "Method", "Mode", "N", "Re", "Scheme", "PressureSolver",
        "Threads", "Ranks", "WallTime_s", "Speedup", "Efficiency", "Status",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def add_speedup(rows: List[Dict[str, object]], resource_col: str) -> None:
    ok_rows = [r for r in rows if r.get("Status") == "ok"]
    if not ok_rows:
        return
    ok_rows.sort(key=lambda r: int(r[resource_col]))
    base_time = float(ok_rows[0]["WallTime_s"])
    base_resource = int(ok_rows[0][resource_col])
    if base_time <= 0:
        return
    for row in rows:
        if row.get("Status") != "ok":
            continue
        wall = float(row["WallTime_s"])
        resource = int(row[resource_col])
        speedup = base_time / wall if wall > 0 else float("nan")
        efficiency = speedup / (resource / base_resource) if resource > 0 else float("nan")
        row["Speedup"] = f"{speedup:.8g}"
        row["Efficiency"] = f"{efficiency:.8g}"


def run_openmp_target(spec: TargetSpec, threads: List[int], args: argparse.Namespace) -> List[Dict[str, object]]:
    if spec.build_cmd is not None:
        subprocess.run(spec.build_cmd, cwd=spec.folder, check=True)
    rows: List[Dict[str, object]] = []
    for t in threads:
        cmd = [
            *spec.run_cmd,
            "--single",
            "--N", str(args.N),
            "--Re", str(args.Re),
            "--scheme", args.scheme,
            "--pressure", args.pressure,
            "--no-fields",
        ]
        if args.maxIter is not None:
            cmd += ["--maxIter", str(args.maxIter)]
        if args.poisson_maxIter is not None:
            cmd += ["--poisson-maxIter", str(args.poisson_maxIter)]
        wall, rc = run_timed(cmd, spec.folder, env={"OMP_NUM_THREADS": str(t)})
        rows.append({
            "Solver": spec.name,
            "Target": spec.key,
            "Method": spec.method,
            "Mode": "single",
            "N": args.N,
            "Re": args.Re,
            "Scheme": args.scheme,
            "PressureSolver": args.pressure,
            "Threads": t,
            "Ranks": "",
            "WallTime_s": f"{wall:.8g}",
            "Speedup": "",
            "Efficiency": "",
            "Status": "ok" if rc == 0 else f"failed:{rc}",
        })
    add_speedup(rows, "Threads")
    write_target_csv(spec.scaling_csv, rows)
    return rows


def mpi_available(target: str) -> bool:
    if shutil.which("mpirun") is None:
        return False
    if target in {"c_mpi", "cpp_mpi"} and shutil.which("mpicc") is None:
        return False
    return True


def run_mpi_target(spec: TargetSpec, ranks: List[int], args: argparse.Namespace) -> List[Dict[str, object]]:
    if not mpi_available(spec.key):
        print(f"Skipping {spec.name}: required MPI command was not found.")
        return []
    if spec.build_cmd is not None:
        subprocess.run(spec.build_cmd, cwd=spec.folder, check=True)
    rows: List[Dict[str, object]] = []
    for r in ranks:
        cmd = ["make", args.mode, f"NP={r}"]
        wall, rc = run_timed(cmd, spec.folder)
        rows.append({
            "Solver": spec.name,
            "Target": spec.key,
            "Method": spec.method,
            "Mode": args.mode,
            "N": "case-list",
            "Re": "case-list",
            "Scheme": "case-list",
            "PressureSolver": "case-list",
            "Threads": "",
            "Ranks": r,
            "WallTime_s": f"{wall:.8g}",
            "Speedup": "",
            "Efficiency": "",
            "Status": "ok" if rc == 0 else f"failed:{rc}",
        })
    add_speedup(rows, "Ranks")
    write_target_csv(spec.scaling_csv, rows)
    return rows


def write_combined(root: Path, rows: List[Dict[str, object]]) -> Path:
    out = root / "comparison" / "results" / "scaling" / "parallel_scaling_summary.csv"
    write_target_csv(out, rows)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OpenMP/MPI scaling checks and write scaling plots.")
    parser.add_argument("--targets", type=parse_targets, default=parse_targets("c_openmp,cpp_openmp"),
                        help="Comma list: c_openmp,cpp_openmp,c_mpi,cpp_mpi,python_mpi")
    parser.add_argument("--threads", type=parse_int_list, default=parse_int_list("1,2,4,8"))
    parser.add_argument("--ranks", type=parse_int_list, default=parse_int_list("1,2,4,8"))
    parser.add_argument("--mode", choices=["smoke", "quick", "medium", "full"], default="smoke",
                        help="MPI case-list mode. OpenMP uses one fixed --single case.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--Re", type=int, default=100)
    parser.add_argument("--scheme", default="upwind")
    parser.add_argument("--pressure", default="RBGS")
    parser.add_argument("--maxIter", type=int, default=None)
    parser.add_argument("--poisson-maxIter", type=int, default=None)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--skip-plots", action="store_true")
    args = parser.parse_args()

    root = repo_root()
    specs = target_specs(root, args.python)
    unknown = [t for t in args.targets if t not in specs]
    if unknown:
        raise SystemExit(f"Unknown targets: {unknown}. Valid targets are: {', '.join(specs)}")

    all_rows: List[Dict[str, object]] = []
    for target in args.targets:
        spec = specs[target]
        if spec.method.startswith("OpenMP"):
            all_rows.extend(run_openmp_target(spec, args.threads, args))
        else:
            all_rows.extend(run_mpi_target(spec, args.ranks, args))

    if not all_rows:
        raise SystemExit("No scaling rows were produced.")
    combined = write_combined(root, all_rows)
    print(f"\nWrote {combined}")

    if not args.skip_plots:
        plot_script = root / "comparison" / "postprocess" / "plot_parallel_scaling.py"
        subprocess.run([args.python, str(plot_script), "--input", str(combined)], cwd=root, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
