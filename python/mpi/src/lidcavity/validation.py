from __future__ import annotations

import math
from typing import List, Tuple

import numpy as np

from .config import Config, Metrics, Result

# -----------------------------------------------------------------------------


def ghia_data(Re: int) -> Tuple[List[float], List[float], List[float], List[float]]:
    if Re == 100:
        return ([1.0000,0.9766,0.9688,0.9609,0.9531,0.8516,0.7344,0.6172,0.5000,0.4531,0.2813,0.1719,0.1016,0.0703,0.0625,0.0547,0.0000],
                [1.0000,0.84123,0.78871,0.73722,0.68717,0.23151,0.00332,-0.13641,-0.20581,-0.21090,-0.15662,-0.10150,-0.06434,-0.04775,-0.04192,-0.03717,0.0000],
                [1.0000,0.9688,0.9609,0.9531,0.9453,0.9063,0.8594,0.8047,0.5000,0.2344,0.2266,0.1563,0.0938,0.0781,0.0703,0.0625,0.0000],
                [0.0000,-0.05906,-0.07391,-0.08864,-0.10313,-0.16914,-0.22445,-0.24533,0.05454,0.17527,0.17507,0.16077,0.12317,0.10890,0.10091,0.09233,0.0000])
    if Re == 400:
        return ([1.0000,0.9766,0.9688,0.9609,0.9531,0.8516,0.7344,0.6172,0.5000,0.4531,0.2813,0.1719,0.1016,0.0703,0.0625,0.0547,0.0000],
                [1.0000,0.75837,0.68439,0.61756,0.55892,0.29093,0.16256,0.02135,-0.11477,-0.17119,-0.32726,-0.24299,-0.14612,-0.10338,-0.09266,-0.08186,0.0000],
                [1.0000,0.9688,0.9609,0.9531,0.9453,0.9063,0.8594,0.8047,0.5000,0.2344,0.2266,0.1563,0.0938,0.0781,0.0703,0.0625,0.0000],
                [0.0000,-0.12146,-0.15663,-0.19254,-0.22847,-0.23827,-0.44993,-0.38598,0.05186,0.30174,0.30203,0.28124,0.22965,0.20920,0.19713,0.18360,0.0000])
    if Re == 1000:
        return ([1.0000,0.9766,0.9688,0.9609,0.9531,0.8516,0.7344,0.6172,0.5000,0.4531,0.2813,0.1719,0.1016,0.0703,0.0625,0.0547,0.0000],
                [1.0000,0.65928,0.57492,0.51117,0.46604,0.33304,0.18719,0.05702,-0.06080,-0.10648,-0.27805,-0.38289,-0.29730,-0.22220,-0.20196,-0.18109,0.0000],
                [1.0000,0.9688,0.9609,0.9531,0.9453,0.9063,0.8594,0.8047,0.5000,0.2344,0.2266,0.1563,0.0938,0.0781,0.0703,0.0625,0.0000],
                [0.0000,-0.21388,-0.27669,-0.33714,-0.39188,-0.51550,-0.42665,-0.31966,0.02526,0.32235,0.33075,0.37095,0.32627,0.30353,0.29012,0.27485,0.0000])
    return [], [], [], []


def interp_linear(x: np.ndarray, y: np.ndarray, q: float) -> float:
    return float(np.interp(q, x, y))


def validate_against_ghia(r: Result, cfg: Config) -> Metrics:
    yu, gu, xv, gv = ghia_data(r.Re)
    if not yu:
        return Metrics()
    N = r.N
    mid = int(math.floor((N + 1) / 2.0 + 0.5)) - 1
    u_center = r.u[:, mid]
    v_center = r.v[mid, :]
    eu = [interp_linear(r.y, u_center, yq) - ref for yq, ref in zip(yu, gu)]
    ev = [interp_linear(r.x, v_center, xq) - ref for xq, ref in zip(xv, gv)]
    u_L2 = math.sqrt(sum(e * e for e in eu) / len(eu))
    v_L2 = math.sqrt(sum(e * e for e in ev) / len(ev))
    u_Linf = max(abs(e) for e in eu)
    v_Linf = max(abs(e) for e in ev)
    if r.Re == 100:
        u_limit, v_limit = cfg.validation_u_L2_limit_Re100, cfg.validation_v_L2_limit_Re100
    elif r.Re == 400:
        u_limit, v_limit = cfg.validation_u_L2_limit_Re400, cfg.validation_v_L2_limit_Re400
    elif r.Re == 1000:
        u_limit, v_limit = cfg.validation_u_L2_limit_Re1000, cfg.validation_v_L2_limit_Re1000
    else:
        u_limit, v_limit = math.inf, math.inf
    return Metrics(True, u_L2 <= u_limit and v_L2 <= v_limit, u_L2, v_L2, u_Linf, v_Linf, u_limit, v_limit)


def quality_label(r: Result, m: Metrics) -> str:
    if r.status == "converged" and m.available and m.passed:
        return "converged_validated"
    if r.status == "converged" and m.available and not m.passed:
        return "converged_not_validated"
    if r.status == "converged" and not m.available:
        return "converged_no_benchmark"
    if r.status != "converged" and m.available and m.passed:
        return "validated_but_not_converged"
    return "needs_improvement"


