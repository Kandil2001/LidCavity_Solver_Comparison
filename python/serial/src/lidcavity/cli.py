from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .config import Config
from .io_utils import summary_header, summary_row, write_field_csv, write_history_csv
from .solver import solve_lid_cavity
from .utils import lower, normalize_implementation, upper
from .validation import quality_label, validate_against_ghia

# -----------------------------------------------------------------------------


def configure_mode(cfg: Config, mode: str) -> None:
    m = lower(mode)
    if m == "quick":
        cfg.meshes = [32, 64]
        cfg.re_list = [100, 400]
        cfg.maxIter = 2000
        cfg.maxIter_N128_bonus = 0
        cfg.maxIter_Re1000_bonus = 0
        cfg.maxIter_central_bonus = 500
        cfg.poisson_maxIter = 1200
    elif m == "medium":
        cfg.meshes = [32, 64]
        cfg.re_list = [100, 400, 1000]
        cfg.maxIter = 3500
        cfg.maxIter_N128_bonus = 0
        cfg.poisson_maxIter = 1800
    elif m == "full":
        pass
    elif m == "single":
        cfg.meshes = [64]
        cfg.re_list = [100]
        cfg.schemes = ["central"]
        cfg.pressure_solvers = ["RBGS"]
        cfg.implementations = ["serial_python_vectorized", "serial_python_looped"]
    elif m == "smoke":
        cfg.meshes = [16]
        cfg.re_list = [100]
        cfg.schemes = ["upwind"]
        cfg.pressure_solvers = ["RBGS"]
        cfg.implementations = ["serial_python_vectorized", "serial_python_looped"]
        cfg.maxIter = 20
        cfg.maxIter_N128_bonus = 0
        cfg.maxIter_Re1000_bonus = 0
        cfg.maxIter_central_bonus = 0
        cfg.poisson_maxIter = 50
    else:
        raise ValueError(f"Unknown mode: {mode} (use quick, medium, full, single, or smoke)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Serial NumPy/Python lid-cavity solver")
    parser.add_argument("--mode", choices=["quick", "medium", "full", "single", "smoke"], default="quick")
    parser.add_argument("--single", action="store_true")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--Re", type=int, default=100)
    parser.add_argument("--scheme", default="central")
    parser.add_argument("--pressure", default="RBGS")
    parser.add_argument("--implementation", default="serial_python_vectorized")
    parser.add_argument("--no-fields", action="store_true")
    parser.add_argument("--maxIter", type=int, default=None)
    parser.add_argument("--poisson-maxIter", type=int, default=None)
    args = parser.parse_args()

    cfg = Config()
    mode = "single" if args.single else args.mode
    configure_mode(cfg, mode)
    if args.single:
        cfg.meshes = [args.N]
        cfg.re_list = [args.Re]
        cfg.schemes = [lower(args.scheme)]
        cfg.pressure_solvers = [upper(args.pressure)]
        cfg.implementations = [normalize_implementation(args.implementation)]
    if args.no_fields:
        cfg.save_fields = False
    if args.maxIter is not None:
        cfg.maxIter = args.maxIter
    if args.poisson_maxIter is not None:
        cfg.poisson_maxIter = args.poisson_maxIter

    Path(cfg.data_dir).mkdir(parents=True, exist_ok=True)
    summary_path = Path(cfg.data_dir) / f"study_summary_{lower(mode)}.csv"
    ncases = len(cfg.meshes) * len(cfg.re_list) * len(cfg.schemes) * len(cfg.pressure_solvers) * len(cfg.implementations)

    print("\nLID-DRIVEN CAVITY PYTHON SOLVER")
    print(f"Mode: {mode}")
    print(f"Total simulations: {ncases}")
    print(f"Summary: {summary_path}\n")

    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(summary_header())
        case_id = 0
        for N in cfg.meshes:
            for Re in cfg.re_list:
                for scheme in cfg.schemes:
                    for pressure_solver in cfg.pressure_solvers:
                        for implementation in cfg.implementations:
                            case_id += 1
                            case_name = f"case_{case_id:03d}_N{N}_Re{Re}_{lower(scheme)}_{upper(pressure_solver)}_{lower(implementation)}"
                            print(f"[{case_id:03d}] N={N} Re={Re} Scheme={scheme} Pressure={pressure_solver} Implementation={implementation}")
                            r = solve_lid_cavity(N, Re, scheme, pressure_solver, implementation, cfg)
                            m = validate_against_ghia(r, cfg)
                            q = quality_label(r, m)
                            writer.writerow(summary_row(case_id, r, m, q))
                            f.flush()
                            write_history_csv(r, case_name, cfg)
                            if cfg.save_fields:
                                write_field_csv(r, case_name, cfg)
                            print(f"      status={r.status} quality={q} iter={r.iterations}/{r.localMaxIter} Rc_mass={r.final_Rc_mass:.3e} Rc_div={r.final_Rc_div:.3e} runtime={r.runtime:.2f}s avgPiter={r.avg_poisson_iters:.1f}")
    print(f"\nFinished. CSV outputs are in {cfg.data_dir}")
    return 0


