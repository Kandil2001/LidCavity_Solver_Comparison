from __future__ import annotations

import math
import sys
from typing import Tuple

import numpy as np

from .config import Config, PoissonInfo, PI
from .utils import lower, upper

# -----------------------------------------------------------------------------


def apply_lid_bc(u: np.ndarray, v: np.ndarray, U_lid: float) -> None:
    u[0, :] = 0.0
    u[-1, :] = U_lid
    u[:, 0] = 0.0
    u[:, -1] = 0.0
    v[0, :] = 0.0
    v[-1, :] = 0.0
    v[:, 0] = 0.0
    v[:, -1] = 0.0


def apply_pressure_bc(p: np.ndarray) -> None:
    p[:, 0] = p[:, 1]
    p[:, -1] = p[:, -2]
    p[0, :] = p[1, :]
    p[-1, :] = p[-2, :]
    p[0, 0] = 0.0


def compute_dt(u: np.ndarray, v: np.ndarray, dx: float, dy: float, nu: float, cfg: Config) -> float:
    max_vel = max(float(np.max(np.abs(u))), float(np.max(np.abs(v))), cfg.U_lid, 1e-12)
    h = min(dx, dy)
    dt_conv = cfg.cfl * h / max_vel
    dt_diff = 0.25 * h * h / nu if nu > 0.0 else math.inf
    return min(dt_conv, dt_diff, cfg.dt_max)


def divergence_field(u: np.ndarray, v: np.ndarray, dx: float, dy: float) -> np.ndarray:
    div = np.zeros_like(u)
    div[1:-1, 1:-1] = ((u[1:-1, 2:] - u[1:-1, :-2]) / (2.0 * dx)
                       + (v[2:, 1:-1] - v[:-2, 1:-1]) / (2.0 * dy))
    return div


def compute_vorticity(u: np.ndarray, v: np.ndarray, dx: float, dy: float) -> np.ndarray:
    omega = np.zeros_like(u)
    omega[1:-1, 1:-1] = ((v[1:-1, 2:] - v[1:-1, :-2]) / (2.0 * dx)
                         - (u[2:, 1:-1] - u[:-2, 1:-1]) / (2.0 * dy))
    return omega


def momentum_predictor(u: np.ndarray, v: np.ndarray, p: np.ndarray, Re: int, scheme: str, cfg: Config) -> Tuple[np.ndarray, np.ndarray, float]:
    N = u.shape[0]
    dx = cfg.L / float(N - 1)
    dy = dx
    nu = cfg.U_lid * cfg.L / float(Re)
    dt = compute_dt(u, v, dx, dy, nu, cfg)
    scheme = lower(scheme)

    u_star = u.copy()
    v_star = v.copy()

    uC = u[1:-1, 1:-1]
    vC = v[1:-1, 1:-1]

    lap_u = ((u[1:-1, 2:] - 2.0 * uC + u[1:-1, :-2]) / (dx * dx)
             + (u[2:, 1:-1] - 2.0 * uC + u[:-2, 1:-1]) / (dy * dy))
    lap_v = ((v[1:-1, 2:] - 2.0 * vC + v[1:-1, :-2]) / (dx * dx)
             + (v[2:, 1:-1] - 2.0 * vC + v[:-2, 1:-1]) / (dy * dy))

    if scheme == "central":
        du_dx = (u[1:-1, 2:] - u[1:-1, :-2]) / (2.0 * dx)
        du_dy = (u[2:, 1:-1] - u[:-2, 1:-1]) / (2.0 * dy)
        dv_dx = (v[1:-1, 2:] - v[1:-1, :-2]) / (2.0 * dx)
        dv_dy = (v[2:, 1:-1] - v[:-2, 1:-1]) / (2.0 * dy)
    elif scheme == "upwind":
        du_dx = np.where(uC >= 0.0, (uC - u[1:-1, :-2]) / dx, (u[1:-1, 2:] - uC) / dx)
        dv_dx = np.where(uC >= 0.0, (vC - v[1:-1, :-2]) / dx, (v[1:-1, 2:] - vC) / dx)
        du_dy = np.where(vC >= 0.0, (uC - u[:-2, 1:-1]) / dy, (u[2:, 1:-1] - uC) / dy)
        dv_dy = np.where(vC >= 0.0, (vC - v[:-2, 1:-1]) / dy, (v[2:, 1:-1] - vC) / dy)
    else:
        raise ValueError(f"Unknown convection scheme: {scheme}")

    conv_u = uC * du_dx + vC * du_dy
    conv_v = uC * dv_dx + vC * dv_dy
    dp_dx = (p[1:-1, 2:] - p[1:-1, :-2]) / (2.0 * dx)
    dp_dy = (p[2:, 1:-1] - p[:-2, 1:-1]) / (2.0 * dy)

    u_pred = uC + dt * (-conv_u - dp_dx + nu * lap_u)
    v_pred = vC + dt * (-conv_v - dp_dy + nu * lap_v)

    u_star[1:-1, 1:-1] = (1.0 - cfg.alpha_u) * uC + cfg.alpha_u * u_pred
    v_star[1:-1, 1:-1] = (1.0 - cfg.alpha_u) * vC + cfg.alpha_u * v_pred
    apply_lid_bc(u_star, v_star, cfg.U_lid)
    return u_star, v_star, dt



def divergence_field_looped(u: np.ndarray, v: np.ndarray, dx: float, dy: float) -> np.ndarray:
    N = u.shape[0]
    div = np.zeros_like(u)
    for i in range(1, N - 1):
        for j in range(1, N - 1):
            div[i, j] = ((u[i, j + 1] - u[i, j - 1]) / (2.0 * dx)
                         + (v[i + 1, j] - v[i - 1, j]) / (2.0 * dy))
    return div


def compute_vorticity_looped(u: np.ndarray, v: np.ndarray, dx: float, dy: float) -> np.ndarray:
    N = u.shape[0]
    omega = np.zeros_like(u)
    for i in range(1, N - 1):
        for j in range(1, N - 1):
            omega[i, j] = ((v[i, j + 1] - v[i, j - 1]) / (2.0 * dx)
                           - (u[i + 1, j] - u[i - 1, j]) / (2.0 * dy))
    return omega


def momentum_predictor_looped(u: np.ndarray, v: np.ndarray, p: np.ndarray, Re: int, scheme: str, cfg: Config) -> Tuple[np.ndarray, np.ndarray, float]:
    N = u.shape[0]
    dx = cfg.L / float(N - 1)
    dy = dx
    nu = cfg.U_lid * cfg.L / float(Re)
    dt = compute_dt(u, v, dx, dy, nu, cfg)
    scheme = lower(scheme)

    u_star = u.copy()
    v_star = v.copy()

    for i in range(1, N - 1):
        for j in range(1, N - 1):
            uC = u[i, j]
            vC = v[i, j]
            lap_u = ((u[i, j + 1] - 2.0 * u[i, j] + u[i, j - 1]) / (dx * dx)
                     + (u[i + 1, j] - 2.0 * u[i, j] + u[i - 1, j]) / (dy * dy))
            lap_v = ((v[i, j + 1] - 2.0 * v[i, j] + v[i, j - 1]) / (dx * dx)
                     + (v[i + 1, j] - 2.0 * v[i, j] + v[i - 1, j]) / (dy * dy))

            if scheme == "central":
                du_dx = (u[i, j + 1] - u[i, j - 1]) / (2.0 * dx)
                du_dy = (u[i + 1, j] - u[i - 1, j]) / (2.0 * dy)
                dv_dx = (v[i, j + 1] - v[i, j - 1]) / (2.0 * dx)
                dv_dy = (v[i + 1, j] - v[i - 1, j]) / (2.0 * dy)
            elif scheme == "upwind":
                if uC >= 0.0:
                    du_dx = (u[i, j] - u[i, j - 1]) / dx
                    dv_dx = (v[i, j] - v[i, j - 1]) / dx
                else:
                    du_dx = (u[i, j + 1] - u[i, j]) / dx
                    dv_dx = (v[i, j + 1] - v[i, j]) / dx
                if vC >= 0.0:
                    du_dy = (u[i, j] - u[i - 1, j]) / dy
                    dv_dy = (v[i, j] - v[i - 1, j]) / dy
                else:
                    du_dy = (u[i + 1, j] - u[i, j]) / dy
                    dv_dy = (v[i + 1, j] - v[i, j]) / dy
            else:
                raise ValueError(f"Unknown convection scheme: {scheme}")

            conv_u = uC * du_dx + vC * du_dy
            conv_v = uC * dv_dx + vC * dv_dy
            dp_dx = (p[i, j + 1] - p[i, j - 1]) / (2.0 * dx)
            dp_dy = (p[i + 1, j] - p[i - 1, j]) / (2.0 * dy)
            u_pred = u[i, j] + dt * (-conv_u - dp_dx + nu * lap_u)
            v_pred = v[i, j] + dt * (-conv_v - dp_dy + nu * lap_v)
            u_star[i, j] = (1.0 - cfg.alpha_u) * u[i, j] + cfg.alpha_u * u_pred
            v_star[i, j] = (1.0 - cfg.alpha_u) * v[i, j] + cfg.alpha_u * v_pred

    apply_lid_bc(u_star, v_star, cfg.U_lid)
    return u_star, v_star, dt

def poisson_true_residual(phi: np.ndarray, rhs: np.ndarray, dx: float, dy: float) -> float:
    lap = ((phi[1:-1, 2:] - 2.0 * phi[1:-1, 1:-1] + phi[1:-1, :-2]) / (dx * dx)
           + (phi[2:, 1:-1] - 2.0 * phi[1:-1, 1:-1] + phi[:-2, 1:-1]) / (dy * dy))
    return float(np.max(np.abs(lap - rhs[1:-1, 1:-1])))


def pressure_poisson(rhs: np.ndarray, dx: float, dy: float, solver_type: str, cfg: Config) -> Tuple[np.ndarray, PoissonInfo]:
    N = rhs.shape[0]
    phi = np.zeros_like(rhs)
    rhs2 = rhs.copy()
    solver_type = upper(solver_type)

    rhs2[1:-1, 1:-1] -= float(np.mean(rhs2[1:-1, 1:-1]))
    den = 2.0 * (dx * dx + dy * dy)

    if lower(cfg.sor_omega) == "auto":
        omega = 2.0 / (1.0 + math.sin(PI / float(N - 1)))
        omega = min(max(omega, cfg.sor_omega_min), cfg.sor_omega_max)
    else:
        omega = float(cfg.sor_omega)

    rhs_norm = max(1.0, float(np.max(np.abs(rhs2[1:-1, 1:-1]))))
    ii, jj = np.indices((N - 2, N - 2))
    red_mask = ((ii + 2) + (jj + 2)) % 2 == 0  # same MATLAB 1-based parity as C++

    converged = False
    final_res = math.inf
    final_change = math.inf
    it = 0

    for it in range(1, cfg.poisson_maxIter + 1):
        phi_old = phi.copy()

        if solver_type == "JACOBI":
            phi_new = phi.copy()
            phi_new[1:-1, 1:-1] = (((phi[2:, 1:-1] + phi[:-2, 1:-1]) * dy * dy
                                    + (phi[1:-1, 2:] + phi[1:-1, :-2]) * dx * dx
                                    - rhs2[1:-1, 1:-1] * dx * dx * dy * dy) / den)
            phi = phi_new
            apply_pressure_bc(phi)
        elif solver_type in {"RBGS", "RBSOR"}:
            for mask in (red_mask, ~red_mask):
                candidate = (((phi[2:, 1:-1] + phi[:-2, 1:-1]) * dy * dy
                              + (phi[1:-1, 2:] + phi[1:-1, :-2]) * dx * dx
                              - rhs2[1:-1, 1:-1] * dx * dx * dy * dy) / den)
                inner = phi[1:-1, 1:-1]
                if solver_type == "RBSOR":
                    inner[mask] = (1.0 - omega) * inner[mask] + omega * candidate[mask]
                else:
                    inner[mask] = candidate[mask]
                phi[1:-1, 1:-1] = inner
                apply_pressure_bc(phi)
        else:
            raise ValueError(f"Unknown pressure solver: {solver_type}")

        final_change = float(np.max(np.abs(phi - phi_old)))
        if it % cfg.poisson_check_every == 0 or it == 1 or it == cfg.poisson_maxIter:
            final_res = poisson_true_residual(phi, rhs2, dx, dy)
            rel_res = final_res / rhs_norm
            if final_res < cfg.poisson_tol_abs or rel_res < cfg.poisson_tol_rel:
                converged = True
                break

    if not converged:
        final_res = poisson_true_residual(phi, rhs2, dx, dy)
    return phi, PoissonInfo(it, converged, final_res, final_res / rhs_norm, final_change, omega)



def poisson_true_residual_looped(phi: np.ndarray, rhs: np.ndarray, dx: float, dy: float) -> float:
    N = phi.shape[0]
    res = 0.0
    for i in range(1, N - 1):
        for j in range(1, N - 1):
            lap = ((phi[i, j + 1] - 2.0 * phi[i, j] + phi[i, j - 1]) / (dx * dx)
                   + (phi[i + 1, j] - 2.0 * phi[i, j] + phi[i - 1, j]) / (dy * dy))
            e = abs(lap - rhs[i, j])
            if e > res:
                res = e
    return float(res)


def pressure_poisson_looped(rhs: np.ndarray, dx: float, dy: float, solver_type: str, cfg: Config) -> Tuple[np.ndarray, PoissonInfo]:
    N = rhs.shape[0]
    phi = np.zeros_like(rhs)
    rhs2 = rhs.copy()
    solver_type = upper(solver_type)

    # Remove the mean only from the interior, matching the C/MATLAB convention.
    interior_sum = 0.0
    count = 0
    for i in range(1, N - 1):
        for j in range(1, N - 1):
            interior_sum += rhs2[i, j]
            count += 1
    interior_mean = interior_sum / float(count) if count else 0.0
    for i in range(1, N - 1):
        for j in range(1, N - 1):
            rhs2[i, j] -= interior_mean

    den = 2.0 * (dx * dx + dy * dy)
    if lower(cfg.sor_omega) == "auto":
        omega = 2.0 / (1.0 + math.sin(PI / float(N - 1)))
        omega = min(max(omega, cfg.sor_omega_min), cfg.sor_omega_max)
    else:
        omega = float(cfg.sor_omega)

    rhs_norm = 1.0
    for i in range(1, N - 1):
        for j in range(1, N - 1):
            rhs_norm = max(rhs_norm, abs(rhs2[i, j]))

    converged = False
    final_res = math.inf
    final_change = math.inf
    it = 0

    for it in range(1, cfg.poisson_maxIter + 1):
        phi_old = phi.copy()

        if solver_type == "JACOBI":
            phi_new = phi.copy()
            for i in range(1, N - 1):
                for j in range(1, N - 1):
                    phi_new[i, j] = (((phi[i + 1, j] + phi[i - 1, j]) * dy * dy
                                      + (phi[i, j + 1] + phi[i, j - 1]) * dx * dx
                                      - rhs2[i, j] * dx * dx * dy * dy) / den)
            phi = phi_new
            apply_pressure_bc(phi)
        elif solver_type in {"RBGS", "RBSOR"}:
            for color in (0, 1):
                for i in range(1, N - 1):
                    for j in range(1, N - 1):
                        is_red = ((i + 1) + (j + 1)) % 2 == 0
                        if (color == 0 and not is_red) or (color == 1 and is_red):
                            continue
                        candidate = (((phi[i + 1, j] + phi[i - 1, j]) * dy * dy
                                      + (phi[i, j + 1] + phi[i, j - 1]) * dx * dx
                                      - rhs2[i, j] * dx * dx * dy * dy) / den)
                        if solver_type == "RBSOR":
                            phi[i, j] = (1.0 - omega) * phi[i, j] + omega * candidate
                        else:
                            phi[i, j] = candidate
                apply_pressure_bc(phi)
        else:
            raise ValueError(f"Unknown pressure solver: {solver_type}")

        final_change = float(np.max(np.abs(phi - phi_old)))
        if it % cfg.poisson_check_every == 0 or it == 1 or it == cfg.poisson_maxIter:
            final_res = poisson_true_residual_looped(phi, rhs2, dx, dy)
            rel_res = final_res / rhs_norm
            if final_res < cfg.poisson_tol_abs or rel_res < cfg.poisson_tol_rel:
                converged = True
                break

    if not converged:
        final_res = poisson_true_residual_looped(phi, rhs2, dx, dy)
    return phi, PoissonInfo(it, converged, final_res, final_res / rhs_norm, final_change, omega)


def velocity_residuals(u: np.ndarray, v: np.ndarray, u_old: np.ndarray, v_old: np.ndarray, dx: float, dy: float, U: float, L: float) -> Tuple[float, float, float, float]:
    Ru = float(np.max(np.abs(u - u_old)))
    Rv = float(np.max(np.abs(v - v_old)))
    div = divergence_field(u, v, dx, dy)
    Rc_div = float(np.max(np.abs(div)))
    Rc_mass = Rc_div * dx * dy / max(U * L, sys.float_info.epsilon)
    return Ru, Rv, Rc_mass, Rc_div



def velocity_residuals_looped(u: np.ndarray, v: np.ndarray, u_old: np.ndarray, v_old: np.ndarray, dx: float, dy: float, U: float, L: float) -> Tuple[float, float, float, float]:
    N = u.shape[0]
    Ru = 0.0
    Rv = 0.0
    for i in range(N):
        for j in range(N):
            Ru = max(Ru, abs(u[i, j] - u_old[i, j]))
            Rv = max(Rv, abs(v[i, j] - v_old[i, j]))
    div = divergence_field_looped(u, v, dx, dy)
    Rc_div = float(np.max(np.abs(div)))
    Rc_mass = Rc_div * dx * dy / max(U * L, sys.float_info.epsilon)
    return float(Ru), float(Rv), float(Rc_mass), float(Rc_div)


# -----------------------------------------------------------------------------
# Main SIMPLE-style solver
