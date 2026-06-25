#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge rank-local MPI case results into one summary CSV.")
    parser.add_argument("--raw", type=Path, default=Path("results/mpi_raw"))
    parser.add_argument("--out", type=Path, default=Path("results/data"))
    parser.add_argument("--prefix", default="mpi_c_case_parallel")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    frames = []
    for path in sorted(args.raw.glob("rank_*/case_*/results/data/study_summary_single.csv")):
        df = pd.read_csv(path)
        df["OriginalImplementation"] = df["Implementation"]
        base = df["OriginalImplementation"].astype(str).str.lower()
        df["Implementation"] = base.map(lambda name: args.prefix if name == "serial_c" else args.prefix + "_" + name.replace("serial_c_", ""))
        frames.append(df)
    if not frames:
        raise SystemExit(f"No MPI summaries found under {args.raw}")
    out = pd.concat(frames, ignore_index=True)
    out["CaseID"] = range(1, len(out) + 1)
    out_path = args.out / "study_summary_mpi.csv"
    out.to_csv(out_path, index=False)
    print(f"Merged {len(out)} MPI case results -> {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
