#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
from pathlib import Path
import sys

try:
    from mpi4py import MPI
except ImportError as exc:
    raise SystemExit("mpi4py is required. Install with: python3 -m pip install mpi4py") from exc

# Import the serial solver functions from this repo.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lid_cavity import Config, configure_mode, solve_lid_cavity, validate_against_ghia, quality_label, summary_header, summary_row, write_history_csv, write_field_csv, lower, upper, normalize_implementation


def build_cases(mode: str):
    cfg = Config()
    configure_mode(cfg, mode)
    cases = []
    for N in cfg.meshes:
        for Re in cfg.re_list:
            for scheme in cfg.schemes:
                for pressure in cfg.pressure_solvers:
                    for impl in cfg.implementations:
                        cases.append((N, Re, scheme, pressure, impl))
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description="MPI case-parallel Python lid-cavity runner")
    parser.add_argument("--mode", choices=["smoke", "quick", "medium", "full"], default="quick")
    parser.add_argument("--no-fields", action="store_true")
    args = parser.parse_args()

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    cases = build_cases(args.mode)
    if rank == 0:
        print(f"MPI case-parallel Python driver: {len(cases)} cases over {size} ranks")

    local_rows = []
    for local_idx, case_idx in enumerate(range(rank, len(cases), size), start=1):
        N, Re, scheme, pressure, impl = cases[case_idx]
        cfg = Config()
        configure_mode(cfg, "single")
        cfg.meshes = [N]
        cfg.re_list = [Re]
        cfg.schemes = [lower(scheme)]
        cfg.pressure_solvers = [upper(pressure)]
        cfg.implementations = [normalize_implementation(impl)]
        cfg.save_fields = not args.no_fields
        cfg.results_dir = f"results/mpi_raw/rank_{rank:03d}/case_{case_idx+1:03d}/results"
        cfg.data_dir = str(Path(cfg.results_dir) / "data")
        Path(cfg.data_dir).mkdir(parents=True, exist_ok=True)

        print(f"[rank {rank}] case {case_idx+1:03d}: N={N} Re={Re} {scheme} {pressure} {impl}")
        r = solve_lid_cavity(N, Re, scheme, pressure, impl, cfg)
        m = validate_against_ghia(r, cfg)
        q = quality_label(r, m)
        original_impl = r.implementation
        r.implementation = "mpi_python_case_parallel_" + original_impl.replace("serial_python_", "")
        case_name = f"case_{case_idx+1:03d}_N{N}_Re{Re}_{lower(scheme)}_{upper(pressure)}_{lower(r.implementation)}"
        write_history_csv(r, case_name, cfg)
        if cfg.save_fields:
            write_field_csv(r, case_name, cfg)
        row = summary_row(case_idx + 1, r, m, q)
        local_rows.append(row)

    gathered = comm.gather(local_rows, root=0)
    if rank == 0:
        out_dir = Path("results/data")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "study_summary_mpi.csv"
        rows = [row for chunk in gathered for row in chunk]
        rows.sort(key=lambda x: int(x[0]))
        with out_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(summary_header())
            w.writerows(rows)
        print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
