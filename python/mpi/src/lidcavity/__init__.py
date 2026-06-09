"""Modular lid-driven cavity solver package."""

from .config import Config, PoissonInfo, Result, Metrics
from .solver import solve_lid_cavity

__all__ = ["Config", "PoissonInfo", "Result", "Metrics", "solve_lid_cavity"]
