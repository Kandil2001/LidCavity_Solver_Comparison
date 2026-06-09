from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List

import numpy as np

PI = math.pi

@dataclass
class Config:
    U_lid: float = 1.0
    L: float = 1.0

    maxIter: int = 4000
    maxIter_N128_bonus: int = 3000
    maxIter_Re1000_bonus: int = 3000
    maxIter_central_bonus: int = 1500

    tol_mass: float = 1e-7
    tol_divergence: float = 2e-3
    tol_velocity: float = 5e-7
    diverged_limit: float = 1e6

    cfl: float = 0.25
    dt_max: float = 0.0025
    dt_min: float = 1e-6

    alpha_u: float = 0.55
    alpha_p: float = 0.20

    poisson_maxIter: int = 2500
    poisson_tol_abs: float = 1e-8
    poisson_tol_rel: float = 1e-4
    poisson_check_every: int = 25

    sor_omega: str = "auto"
    sor_omega_min: float = 1.15
    sor_omega_max: float = 1.90

    meshes: List[int] = field(default_factory=lambda: [32, 64, 128])
    re_list: List[int] = field(default_factory=lambda: [100, 400, 1000])
    schemes: List[str] = field(default_factory=lambda: ["upwind", "central"])
    pressure_solvers: List[str] = field(default_factory=lambda: ["RBGS", "RBSOR"])
    implementations: List[str] = field(default_factory=lambda: ["serial_python_vectorized", "serial_python_looped"])

    validation_u_L2_limit_Re100: float = 0.030
    validation_v_L2_limit_Re100: float = 0.030
    validation_u_L2_limit_Re400: float = 0.090
    validation_v_L2_limit_Re400: float = 0.120
    validation_u_L2_limit_Re1000: float = 0.160
    validation_v_L2_limit_Re1000: float = 0.180

    save_fields: bool = True
    results_dir: str = "results"
    data_dir: str = "results/data"


@dataclass
class PoissonInfo:
    iter: int = 0
    converged: bool = False
    final_true_residual: float = math.inf
    final_relative_residual: float = math.inf
    final_change: float = math.inf
    omega: float = 1.0


@dataclass
class Result:
    N: int
    Re: int
    scheme: str
    pressure_solver: str
    implementation: str
    localMaxIter: int
    x: np.ndarray
    y: np.ndarray
    u: np.ndarray
    v: np.ndarray
    p: np.ndarray
    speed: np.ndarray
    vorticity: np.ndarray
    Ru: List[float]
    Rv: List[float]
    Rc_mass: List[float]
    Rc_div: List[float]
    dt: List[float]
    poisson_iters: List[int]
    poisson_relative_residual: List[float]
    poisson_converged: List[bool]
    iterations: int
    runtime: float
    status: str
    final_Ru: float
    final_Rv: float
    final_Rc_mass: float
    final_Rc_div: float
    avg_poisson_iters: float
    avg_poisson_relative_residual: float
    pressure_saturation_ratio: float
    stagnation_counter: int


@dataclass
class Metrics:
    available: bool = False
    passed: bool = False
    u_L2: float = math.nan
    v_L2: float = math.nan
    u_Linf: float = math.nan
    v_Linf: float = math.nan
    u_limit: float = math.nan
    v_limit: float = math.nan


# -----------------------------------------------------------------------------
# Small utilities
