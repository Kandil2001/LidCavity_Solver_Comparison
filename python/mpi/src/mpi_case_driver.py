#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

from mpi4py import MPI

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lidcavity.config import Config
from lidcavity.cli import configure_mode
from lidcavity.solver import solve_lid_cavity
from lidcavity.validation import validate_against_ghia, quality_label
from lidcavity.io_utils import summary_header, summary_row, write_history_csv, write_field_csv
from lidcavity.utils import lower, upper, normalize_implementation


def build_cases(mode: str):
    cfg = Config()
    configure_mode(cfg, mode)

    cases = []
    case_id = 0

    for N in cfg.meshes:
        for Re in cfg.re_list:
            for scheme in cfg.schemes:
                for pressure in cfg.pressure_solvers:
                    for impl in cfg.implementations:
                        case_id += 1
                        cases.append((case_id, N, Re, scheme, pressure, impl))

    return cases


def append_row(path: Path, header, row):
    new_file = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(header)
        w.writerow(row)


def merge_rank_files(part: str):
    out_dir = Path("results/data")
    out_dir.mkdir(parents=True, exist_ok=True)

    rank_files = sorted(out_dir.glob(f"study_summary_mpi_part_{part}_rank_*.csv"))
    out_path = out_dir / f"study_summary_mpi_part_{part}.csv"

    rows = []
    header = None

    for rf in rank_files:
        with rf.open("r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            file_header = next(reader, None)
            if file_header and header is None:
                header = file_header
            for row in reader:
                if row:
                    rows.append(row)

    if header is None:
        header = summary_header()

    # Deduplicate by case id, keep last
    by_case = {}
    for row in rows:
        by_case[int(row[0])] = row

    rows = [by_case[k] for k in sorted(by_case)]

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

    print(f"Wrote {out_path}")
    print(f"Rows written: {len(rows)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe checkpointed MPI case-parallel Python lid-cavity runner")
    parser.add_argument("--mode", choices=["smoke", "quick", "medium", "full"], default="full")
    parser.add_argument("--no-fields", action="store_true")
    parser.add_argument("--case-start", type=int, default=1)
    parser.add_argument("--case-end", type=int, default=None)
    parser.add_argument("--part", type=str, default="000")
    args = parser.parse_args()

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    all_cases = build_cases(args.mode)
    total_cases = len(all_cases)

    case_end = args.case_end if args.case_end is not None else total_cases
    selected = [c for c in all_cases if args.case_start <= c[0] <= case_end]

    if rank == 0:
        print("Python MPI checkpointed driver")
        print(f"Total cases in mode {args.mode}: {total_cases}")
        print(f"Selected cases: {args.case_start} to {case_end}")
        print(f"Selected count: {len(selected)}")
        print(f"MPI ranks: {size}", flush=True)

    local_path = Path("results/data") / f"study_summary_mpi_part_{args.part}_rank_{rank:03d}.csv"

    for local_index in range(rank, len(selected), size):
        case_id, N, Re, scheme, pressure, impl = selected[local_index]

        cfg = Config()
        configure_mode(cfg, "single")
        cfg.meshes = [N]
        cfg.re_list = [Re]
        cfg.schemes = [lower(scheme)]
        cfg.pressure_solvers = [upper(pressure)]
        cfg.implementations = [normalize_implementation(impl)]
        cfg.save_fields = not args.no_fields

        cfg.results_dir = f"results/mpi_raw/part_{args.part}/rank_{rank:03d}/case_{case_id:03d}/results"
        cfg.data_dir = str(Path(cfg.results_dir) / "data")
        Path(cfg.data_dir).mkdir(parents=True, exist_ok=True)

        print(
            f"[rank {rank}] case {case_id:03d}: "
            f"N={N} Re={Re} scheme={scheme} pressure={pressure} impl={impl}",
            flush=True,
        )

        r = solve_lid_cavity(N, Re, scheme, pressure, impl, cfg)
        m = validate_against_ghia(r, cfg)
        q = quality_label(r, m)

        original_impl = r.implementation
        r.implementation = "mpi_python_case_parallel_" + original_impl.replace("serial_python_", "")

        case_name = f"case_{case_id:03d}_N{N}_Re{Re}_{lower(scheme)}_{upper(pressure)}_{lower(r.implementation)}"

        write_history_csv(r, case_name, cfg)
        if cfg.save_fields:
            write_field_csv(r, case_name, cfg)

        row = summary_row(case_id, r, m, q)
        append_row(local_path, summary_header(), row)

        print(f"[rank {rank}] finished case {case_id:03d} and checkpointed row", flush=True)

    comm.Barrier()

    if rank == 0:
        merge_rank_files(args.part)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
