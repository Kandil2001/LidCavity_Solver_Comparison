#!/usr/bin/env python3
"""Run a small CUDA block-size performance sweep and create CSV/plots.

This is not the same as MPI/OpenMP strong scaling. It measures how the CUDA
prototype runtime changes when the GPU thread-block size is changed for one
fixed case.
"""
from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_int_list(raw: str) -> List[int]:
    vals = [int(x.strip()) for x in raw.split(",") if x.strip()]
    if not vals:
        raise argparse.ArgumentTypeError("Provide at least one integer value")
    if any(v <= 0 for v in vals):
        raise argparse.ArgumentTypeError("All values must be positive")
    return sorted(dict.fromkeys(vals))


def run(cmd: List[str], cwd: Path, check: bool = False) -> subprocess.CompletedProcess:
    print(f"$ (cd {cwd} && {' '.join(cmd)})", flush=True)
    return subprocess.run(cmd, cwd=cwd, check=check)


def run_timed(cmd: List[str], cwd: Path) -> tuple[float, int]:
    start = time.perf_counter()
    proc = run(cmd, cwd, check=False)
    return time.perf_counter() - start, proc.returncode


def cuda_available(require_gpu: bool) -> tuple[bool, str]:
    if shutil.which("nvcc") is None:
        return False, "nvcc was not found"
    if require_gpu:
        smi = shutil.which("nvidia-smi")
        if smi is None:
            return False, "nvidia-smi was not found, so no runnable NVIDIA GPU was detected"
        proc = subprocess.run([smi], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if proc.returncode != 0:
            return False, "nvidia-smi exists but no accessible NVIDIA GPU was detected"
    return True, "CUDA toolkit/GPU check passed"


def add_speedup(rows: List[Dict[str, object]]) -> None:
    ok = [r for r in rows if r.get("Status") == "ok"]
    if not ok:
        return
    ok.sort(key=lambda r: int(r["BlockSize"]))
    base_time = float(ok[0]["WallTime_s"])
    base_block = int(ok[0]["BlockSize"])
    if base_time <= 0 or base_block <= 0:
        return
    for row in rows:
        if row.get("Status") != "ok":
            continue
        wall = float(row["WallTime_s"])
        block = int(row["BlockSize"])
        speedup = base_time / wall if wall > 0 else float("nan")
        # This is a tuning efficiency, not classical parallel efficiency.
        efficiency = speedup / (block / base_block) if block > 0 else float("nan")
        row["Speedup"] = f"{speedup:.8g}"
        row["Efficiency"] = f"{efficiency:.8g}"


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "Solver", "Target", "Method", "Mode", "N", "Re", "Scheme", "PressureSolver",
        "Threads", "Ranks", "BlockSize", "WallTime_s", "Speedup", "Efficiency", "Status",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in cols})


def main() -> int:
    ap = argparse.ArgumentParser(description="Run CUDA block-size performance sweep")
    ap.add_argument("--block-sizes", type=parse_int_list, default=parse_int_list("64,128,256"))
    ap.add_argument("--N", type=int, default=64)
    ap.add_argument("--Re", type=int, default=100)
    ap.add_argument("--scheme", default="upwind")
    ap.add_argument("--pressure", default="JACOBI")
    ap.add_argument("--maxIter", type=int, default=200)
    ap.add_argument("--poisson-maxIter", type=int, default=150)
    ap.add_argument("--no-fields", action="store_true", default=True)
    ap.add_argument("--require-gpu", action="store_true", default=True)
    ap.add_argument("--skip-if-missing", action="store_true", help="Exit 0 instead of failing when CUDA is unavailable")
    ap.add_argument("--skip-plots", action="store_true")
    args = ap.parse_args()

    root = repo_root()
    cuda_dir = root / "cuda"
    ok, reason = cuda_available(args.require_gpu)
    if not ok:
        msg = f"Skipping CUDA scaling: {reason}."
        if args.skip_if_missing:
            print(msg)
            return 0
        raise SystemExit(msg)

    run(["make", "build"], cuda_dir, check=True)
    exe = cuda_dir / "bin" / "lid_cavity_cuda"
    rows: List[Dict[str, object]] = []
    for block in args.block_sizes:
        cmd = [
            str(exe),
            "--N", str(args.N),
            "--Re", str(args.Re),
            "--scheme", args.scheme,
            "--pressure", args.pressure,
            "--maxIter", str(args.maxIter),
            "--poisson-maxIter", str(args.poisson_maxIter),
            "--block-size", str(block),
        ]
        if args.no_fields:
            cmd.append("--no-fields")
        wall, rc = run_timed(cmd, cuda_dir)
        rows.append({
            "Solver": "CUDA prototype",
            "Target": "cuda",
            "Method": "CUDA block-size sweep",
            "Mode": "single",
            "N": args.N,
            "Re": args.Re,
            "Scheme": args.scheme,
            "PressureSolver": args.pressure,
            "Threads": "",
            "Ranks": "",
            "BlockSize": block,
            "WallTime_s": f"{wall:.8g}",
            "Speedup": "",
            "Efficiency": "",
            "Status": "ok" if rc == 0 else f"failed:{rc}",
        })
    add_speedup(rows)

    out = cuda_dir / "results" / "scaling" / "cuda_block_size_scaling.csv"
    write_csv(out, rows)
    print(f"Wrote {out.relative_to(root)}")

    combined = root / "comparison" / "results" / "scaling" / "cuda_scaling_summary.csv"
    write_csv(combined, rows)
    print(f"Wrote {combined.relative_to(root)}")

    if not args.skip_plots:
        plot_script = root / "comparison" / "postprocess" / "plot_parallel_scaling.py"
        subprocess.run([sys.executable, str(plot_script), "--input", str(out)], cwd=root, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
