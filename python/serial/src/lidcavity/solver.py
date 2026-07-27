from __future__ import annotations

import math
import time
from typing import List

import numpy as np

from .config import Config, Result
from .operators import (
    apply_lid_bc,
    compute_vorticity,
    compute_vorticity_looped,
    divergence_field,
    divergence_field_looped,
    momentum_predictor,
    momentum_predictor_looped,
    pressure_poisson,
    pressure_poisson_looped,
    velocity_residuals,
    velocity_residuals_looped,
)
from .utils import lower, normalize_implementation, upper

# -----------------------------------------------------------------------------


def solve_lid_cavity(N: int, Re: int, scheme: str, pressure_solver: str, implementation: str, cfg: Config) -> Result:
    scheme = lower(scheme)
    pressure_solver = upper(pressure_solver)
    implementation = normalize_implementation(implementation)
    use_looped = implementation == "serial_python_looped"
    dx = cfg.L / float(N - 1)
    dy = dx

    localMaxIter = cfg.maxIter
    if N >= 128:
        localMaxIter += cfg.maxIter_N128_bonus
    if Re >= 1000:
        localMaxIter += cfg.maxIter_Re1000_bonus
    if scheme == "central":
        localMaxIter += cfg.maxIter_central_bonus

    u = np.zeros((N, N), dtype=float)
    v = np.zeros((N, N), dtype=float)
    p = np.zeros((N, N), dtype=float)
    apply_lid_bc(u, v, cfg.U_lid)

    Ru_hist: List[float] = []
    Rv_hist: List[float] = []
    Rc_mass_hist: List[float] = []
    Rc_div_hist: List[float] = []
    dt_hist: List[float] = []
    piter_hist: List[int] = []
    prel_hist: List[float] = []
    pconv_hist: List[bool] = []

    status = "maxIter"
    stagnation_counter = 0
    prev_mass = math.inf
    iter_done = 0
    t0 = time.perf_counter()

    for iteration in range(1, localMaxIter + 1):
        iter_done = iteration
        u_old = u.copy()
        v_old = v.copy()

        if use_looped:
            u_star, v_star, dt = momentum_predictor_looped(u, v, p, Re, scheme, cfg)
            dt = max(dt, cfg.dt_min)
            rhs = divergence_field_looped(u_star, v_star, dx, dy) / dt
            p_prime, pinfo = pressure_poisson_looped(rhs, dx, dy, pressure_solver, cfg)

            u = u_star.copy()
            v = v_star.copy()
            for i in range(1, N - 1):
                for j in range(1, N - 1):
                    u[i, j] = u_star[i, j] - dt * (p_prime[i, j + 1] - p_prime[i, j - 1]) / (2.0 * dx)
                    v[i, j] = v_star[i, j] - dt * (p_prime[i + 1, j] - p_prime[i - 1, j]) / (2.0 * dy)

            p += cfg.alpha_p * p_prime
            p -= float(np.mean(p))
            apply_lid_bc(u, v, cfg.U_lid)
            Ru, Rv, Rc_mass, Rc_div = velocity_residuals_looped(u, v, u_old, v_old, dx, dy, cfg.U_lid, cfg.L)
        else:
            u_star, v_star, dt = momentum_predictor(u, v, p, Re, scheme, cfg)
            dt = max(dt, cfg.dt_min)
            rhs = divergence_field(u_star, v_star, dx, dy) / dt
            p_prime, pinfo = pressure_poisson(rhs, dx, dy, pressure_solver, cfg)

            u = u_star.copy()
            v = v_star.copy()
            u[1:-1, 1:-1] = u_star[1:-1, 1:-1] - dt * (p_prime[1:-1, 2:] - p_prime[1:-1, :-2]) / (2.0 * dx)
            v[1:-1, 1:-1] = v_star[1:-1, 1:-1] - dt * (p_prime[2:, 1:-1] - p_prime[:-2, 1:-1]) / (2.0 * dy)

            p += cfg.alpha_p * p_prime
            p -= float(np.mean(p))
            apply_lid_bc(u, v, cfg.U_lid)
            Ru, Rv, Rc_mass, Rc_div = velocity_residuals(u, v, u_old, v_old, dx, dy, cfg.U_lid, cfg.L)
        Ru_hist.append(Ru)
        Rv_hist.append(Rv)
        Rc_mass_hist.append(Rc_mass)
        Rc_div_hist.append(Rc_div)
        dt_hist.append(dt)
        piter_hist.append(pinfo.iter)
        prel_hist.append(pinfo.final_relative_residual)
        pconv_hist.append(pinfo.converged)

        if (not np.isfinite(u).all()) or (not np.isfinite(v).all()) or (not np.isfinite(p).all()) or max(Ru, Rv, Rc_div) > cfg.diverged_limit:
            status = "diverged"
            break

        if Rc_mass > 0.995 * prev_mass:
            stagnation_counter += 1
        else:
            stagnation_counter = 0
        prev_mass = Rc_mass

        if Rc_mass < cfg.tol_mass and max(Ru, Rv) < cfg.tol_velocity:
            status = "converged"
            break

    runtime = time.perf_counter() - t0
    x = np.linspace(0.0, cfg.L, N)
    y = x.copy()
    speed = np.sqrt(u * u + v * v)
    vorticity = compute_vorticity_looped(u, v, dx, dy) if use_looped else compute_vorticity(u, v, dx, dy)
    avg_pi = float(np.mean(piter_hist)) if piter_hist else 0.0
    avg_pr = float(np.mean(prel_hist)) if prel_hist else 0.0
    psat = float(np.mean(np.asarray(piter_hist) >= cfg.poisson_maxIter)) if piter_hist else 0.0

    return Result(
        N, Re, scheme, pressure_solver, implementation, localMaxIter, x, y, u, v, p, speed, vorticity,
        Ru_hist, Rv_hist, Rc_mass_hist, Rc_div_hist, dt_hist, piter_hist, prel_hist, pconv_hist,
        iter_done, runtime, status,
        Ru_hist[-1] if Ru_hist else 0.0,
        Rv_hist[-1] if Rv_hist else 0.0,
        Rc_mass_hist[-1] if Rc_mass_hist else 0.0,
        Rc_div_hist[-1] if Rc_div_hist else 0.0,
        avg_pi, avg_pr, psat, stagnation_counter,
    )


# -----------------------------------------------------------------------------
# Validation and CSV export
