#!/usr/bin/env python3
"""Run the earlier C/C++ OpenMP reference scaling check.

Spatial MPI and hybrid scaling use ``scripts/run_strong_scaling_all.sh`` and the
implementations under ``src/``. Parameter-sweep scheduling is intentionally not supported as an MPI solver target.
"""
from __future__ import annotations

import argparse
import csv
import os
import subprocess
import time
from pathlib import Path


def parse_int_list(raw: str) -> list[int]:
    values = sorted({int(item.strip()) for item in raw.split(",") if item.strip()})
    if not values or any(value < 1 for value in values):
        raise argparse.ArgumentTypeError("Provide positive comma-separated integers")
    return values


def run_target(folder: Path, binary: str, label: str, threads: list[int], args: argparse.Namespace) -> list[dict[str, object]]:
    subprocess.run(["make", "build"], cwd=folder, check=True)
    rows: list[dict[str, object]] = []
    for count in threads:
        command = [
            binary, "--single", "--N", str(args.N), "--Re", str(args.Re),
            "--scheme", args.scheme, "--pressure", args.pressure, "--no-fields",
        ]
        environment = os.environ.copy()
        environment["OMP_NUM_THREADS"] = str(count)
        start = time.perf_counter()
        result = subprocess.run(command, cwd=folder, env=environment)
        elapsed = time.perf_counter() - start
        rows.append({"solver": label, "threads": count, "wall_time_s": elapsed, "status": result.returncode})

    successful = [row for row in rows if row["status"] == 0]
    if successful:
        baseline = min(successful, key=lambda row: int(row["threads"]))
        for row in successful:
            speedup = float(baseline["wall_time_s"]) / float(row["wall_time_s"])
            row["speedup"] = speedup
            row["efficiency"] = speedup / (int(row["threads"]) / int(baseline["threads"]))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Run C/C++ OpenMP reference scaling.")
    parser.add_argument("--threads", type=parse_int_list, default=parse_int_list("1,2,4,8"))
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--Re", type=int, default=100)
    parser.add_argument("--scheme", default="upwind")
    parser.add_argument("--pressure", default="RBGS")
    parser.add_argument("--output", type=Path, default=Path("comparison/results/scaling/openmp_reference_scaling.csv"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    rows = []
    rows += run_target(root / "c/openmp", "./bin/lid_cavity_c_openmp", "C OpenMP reference", args.threads, args)
    rows += run_target(root / "cpp/openmp", "./bin/lid_cavity_openmp", "C++ OpenMP reference", args.threads, args)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["solver", "threads", "wall_time_s", "speedup", "efficiency", "status"]
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    print(f"Wrote {args.output}")
    return 0 if all(row["status"] == 0 for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
