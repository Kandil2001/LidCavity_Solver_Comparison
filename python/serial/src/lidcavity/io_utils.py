from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from .config import Config, Metrics, Result

def write_field_csv(r: Result, case_name: str, cfg: Config) -> None:
    path = Path(cfg.data_dir) / f"{case_name}_fields.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["i", "j", "x", "y", "u", "v", "p", "speed", "vorticity"])
        for i in range(r.N):
            for j in range(r.N):
                w.writerow([i, j, f"{r.x[j]:.12g}", f"{r.y[i]:.12g}", f"{r.u[i,j]:.12g}", f"{r.v[i,j]:.12g}",
                            f"{r.p[i,j]:.12g}", f"{r.speed[i,j]:.12g}", f"{r.vorticity[i,j]:.12g}"])


def write_history_csv(r: Result, case_name: str, cfg: Config) -> None:
    path = Path(cfg.data_dir) / f"{case_name}_history.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["iter", "Ru", "Rv", "Rc_mass", "Rc_div", "dt", "poisson_iters", "poisson_relative_residual", "poisson_converged"])
        for k in range(len(r.Ru)):
            w.writerow([k + 1, f"{r.Ru[k]:.12g}", f"{r.Rv[k]:.12g}", f"{r.Rc_mass[k]:.12g}", f"{r.Rc_div[k]:.12g}",
                        f"{r.dt[k]:.12g}", r.poisson_iters[k], f"{r.poisson_relative_residual[k]:.12g}", int(r.poisson_converged[k])])


def summary_header() -> List[str]:
    return ["CaseID", "Implementation", "N", "Re", "Scheme", "PressureSolver", "Status", "Quality", "Iterations", "LocalMaxIter",
            "FinalRu", "FinalRv", "FinalRcMass", "FinalRcDiv", "Runtime_s", "AvgPoissonIterations",
            "AvgPoissonRelResidual", "PressureSaturationRatio", "HasGhia", "ValidationPass",
            "Ghia_u_L2", "Ghia_v_L2", "Ghia_u_Linf", "Ghia_v_Linf", "Ghia_u_L2_Limit", "Ghia_v_L2_Limit"]


def summary_row(case_id: int, r: Result, m: Metrics, quality: str) -> List[object]:
    return [case_id, r.implementation, r.N, r.Re, r.scheme, r.pressure_solver, r.status, quality, r.iterations, r.localMaxIter,
            f"{r.final_Ru:.12g}", f"{r.final_Rv:.12g}", f"{r.final_Rc_mass:.12g}", f"{r.final_Rc_div:.12g}", f"{r.runtime:.12g}",
            f"{r.avg_poisson_iters:.12g}", f"{r.avg_poisson_relative_residual:.12g}", f"{r.pressure_saturation_ratio:.12g}",
            int(m.available), int(m.passed), f"{m.u_L2:.12g}", f"{m.v_L2:.12g}", f"{m.u_Linf:.12g}", f"{m.v_Linf:.12g}",
            f"{m.u_limit:.12g}", f"{m.v_limit:.12g}"]


# -----------------------------------------------------------------------------
# Command-line interface
