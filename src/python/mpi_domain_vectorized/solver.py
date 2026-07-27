#!/usr/bin/env python3
"""
Python MPI domain-decomposition lid-driven cavity solver

This is a true row-wise domain-decomposition solver: one CFD domain is split
across MPI ranks. It is not a case-level parameter sweep.

Kernel style: NumPy vectorized local slice kernels
Hybrid mode: mpi4py only
"""
from __future__ import annotations
import argparse
import os
import time
import numpy as np
from mpi4py import MPI

KERNEL_STYLE = "vectorized"
IMPLEMENTATION = "python_mpi_domain_vectorized"
HYBRID = False

try:
    from numba import njit, prange, set_num_threads, get_num_threads
    NUMBA_AVAILABLE = True
except Exception:
    NUMBA_AVAILABLE = False
    def set_num_threads(n):
        return None
    def get_num_threads():
        return 1
    def njit(*args, **kwargs):
        def dec(fn): return fn
        return dec
    prange = range


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--N", type=int, default=64)
    p.add_argument("--Re", type=int, default=100)
    p.add_argument("--steps", type=int, default=2000)
    p.add_argument("--poisson-iters", type=int, default=250)
    p.add_argument("--poisson-tol", type=float, default=1e-6)
    p.add_argument("--poisson-solver", "--pressure", dest="poisson_solver", choices=["jacobi", "RBGS", "RBSOR", "rbgs", "rbsor", "sor"], default="RBGS")
    p.add_argument("--sor-omega", type=float, default=1.7)
    p.add_argument("--scheme", choices=["upwind", "central"], default="upwind")
    p.add_argument("--out-dir", default="results/data")
    p.add_argument("--no-fields", action="store_true")
    p.add_argument("--max-dt", type=float, default=0.0025)
    p.add_argument("--cfl", type=float, default=0.25)
    p.add_argument("--threads", type=int, default=int(os.environ.get("NUMBA_NUM_THREADS", "1")))
    args = p.parse_args()
    _norm_poisson_solver(args)
    return args


def _norm_poisson_solver(args):
    args.poisson_solver = str(args.poisson_solver).lower()
    if args.poisson_solver == "sor":
        args.poisson_solver = "rbsor"
    return args.poisson_solver

def decomp(N, rank, size):
    base = N // size
    rem = N % size
    local_n = base + (1 if rank < rem else 0)
    row_start = rank * base + min(rank, rem)
    below = rank - 1 if rank > 0 else MPI.PROC_NULL
    above = rank + 1 if rank < size - 1 else MPI.PROC_NULL
    return row_start, local_n, below, above


def exchange(f, below, above, comm):
    comm.Sendrecv(np.ascontiguousarray(f[1, :]), dest=below, sendtag=10, recvbuf=f[-1, :], source=above, recvtag=10)
    comm.Sendrecv(np.ascontiguousarray(f[-2, :]), dest=above, sendtag=20, recvbuf=f[0, :], source=below, recvtag=20)


def interior_bounds(row_start, local_n, N):
    lo = 1 + (1 if row_start == 0 else 0)
    hi = local_n + 1 - (1 if row_start + local_n == N else 0)
    return lo, hi


def apply_psi_bc(psi, row_start, local_n, N):
    psi[1:local_n+1, 0] = 0.0
    psi[1:local_n+1, -1] = 0.0
    if row_start == 0:
        psi[1, :] = 0.0
    if row_start + local_n == N:
        psi[local_n, :] = 0.0


def apply_omega_bc(omega, psi, row_start, local_n, N, U=1.0):
    h = 1.0 / (N - 1)
    h2 = h * h
    omega[1:local_n+1, 0] = -2.0 * psi[1:local_n+1, 1] / h2
    omega[1:local_n+1, -1] = -2.0 * psi[1:local_n+1, -2] / h2
    if row_start == 0:
        omega[1, 1:-1] = -2.0 * psi[2, 1:-1] / h2
    if row_start + local_n == N:
        omega[local_n, 1:-1] = -2.0 * psi[local_n - 1, 1:-1] / h2 - 2.0 * U / h


def solve_poisson_looped(psi, omega, args, row_start, local_n, below, above, comm):
    N = args.N
    h = 1.0 / (N - 1)
    h2 = h * h
    global_change = np.inf
    lo, hi = interior_bounds(row_start, local_n, N)
    method = _norm_poisson_solver(args)
    if method == "jacobi":
        nxt = psi.copy()
        for _ in range(args.poisson_iters):
            exchange(psi, below, above, comm)
            apply_psi_bc(psi, row_start, local_n, N)
            local_change = 0.0
            for li in range(lo, hi):
                for j in range(1, N - 1):
                    val = 0.25 * (psi[li + 1, j] + psi[li - 1, j] + psi[li, j + 1] + psi[li, j - 1] + h2 * omega[li, j])
                    ch = abs(val - psi[li, j])
                    if ch > local_change: local_change = ch
                    nxt[li, j] = val
            psi, nxt = nxt, psi
            apply_psi_bc(psi, row_start, local_n, N)
            global_change = comm.allreduce(local_change, op=MPI.MAX)
            if global_change < args.poisson_tol: break
        return psi, global_change
    relax = args.sor_omega if method == "rbsor" else 1.0
    for _ in range(args.poisson_iters):
        local_change = 0.0
        exchange(psi, below, above, comm)
        apply_psi_bc(psi, row_start, local_n, N)
        for color in (0, 1):
            for li in range(lo, hi):
                gi = row_start + li - 1
                for j in range(1, N - 1):
                    if ((gi + j) & 1) != color:
                        continue
                    gs = 0.25 * (psi[li + 1, j] + psi[li - 1, j] + psi[li, j + 1] + psi[li, j - 1] + h2 * omega[li, j])
                    old = psi[li, j]
                    val = (1.0 - relax) * old + relax * gs
                    ch = abs(val - old)
                    if ch > local_change: local_change = ch
                    psi[li, j] = val
            apply_psi_bc(psi, row_start, local_n, N)
            exchange(psi, below, above, comm)
        global_change = comm.allreduce(local_change, op=MPI.MAX)
        if global_change < args.poisson_tol: break
    return psi, global_change


def solve_poisson_vectorized(psi, omega, args, row_start, local_n, below, above, comm):
    N = args.N
    h = 1.0 / (N - 1)
    h2 = h * h
    global_change = np.inf
    lo, hi = interior_bounds(row_start, local_n, N)
    method = _norm_poisson_solver(args)
    if method == "jacobi":
        nxt = psi.copy()
        for _ in range(args.poisson_iters):
            exchange(psi, below, above, comm)
            apply_psi_bc(psi, row_start, local_n, N)
            local_change = 0.0
            if lo < hi:
                vals = 0.25 * (psi[lo + 1:hi + 1, 1:-1] + psi[lo - 1:hi - 1, 1:-1] + psi[lo:hi, 2:] + psi[lo:hi, :-2] + h2 * omega[lo:hi, 1:-1])
                local_change = float(np.max(np.abs(vals - psi[lo:hi, 1:-1])))
                nxt[lo:hi, 1:-1] = vals
            psi, nxt = nxt, psi
            apply_psi_bc(psi, row_start, local_n, N)
            global_change = comm.allreduce(local_change, op=MPI.MAX)
            if global_change < args.poisson_tol: break
        return psi, global_change
    relax = args.sor_omega if method == "rbsor" else 1.0
    for _ in range(args.poisson_iters):
        exchange(psi, below, above, comm)
        apply_psi_bc(psi, row_start, local_n, N)
        local_change = 0.0
        if lo < hi:
            I = np.arange(lo, hi)[:, None]
            J = np.arange(1, N - 1)[None, :]
            GI = row_start + I - 1
            block = psi[lo:hi, 1:-1]
            for color in (0, 1):
                mask = ((GI + J) & 1) == color
                gs = 0.25 * (psi[lo + 1:hi + 1, 1:-1] + psi[lo - 1:hi - 1, 1:-1] + psi[lo:hi, 2:] + psi[lo:hi, :-2] + h2 * omega[lo:hi, 1:-1])
                vals = (1.0 - relax) * block + relax * gs
                if np.any(mask):
                    local_change = max(local_change, float(np.max(np.abs(vals[mask] - block[mask]))))
                    block[mask] = vals[mask]
                apply_psi_bc(psi, row_start, local_n, N)
                exchange(psi, below, above, comm)
        global_change = comm.allreduce(local_change, op=MPI.MAX)
        if global_change < args.poisson_tol: break
    return psi, global_change


def velocity_looped(psi, row_start, local_n, N):
    h = 1.0 / (N - 1)
    u = np.zeros_like(psi)
    v = np.zeros_like(psi)
    local_umax = 0.0
    lo, hi = interior_bounds(row_start, local_n, N)
    if row_start + local_n == N:
        u[local_n, :] = 1.0
        local_umax = 1.0
    for li in range(lo, hi):
        for j in range(1, N - 1):
            uu = (psi[li + 1, j] - psi[li - 1, j]) / (2 * h)
            vv = -(psi[li, j + 1] - psi[li, j - 1]) / (2 * h)
            u[li, j] = uu
            v[li, j] = vv
            sp = (uu * uu + vv * vv) ** 0.5
            if sp > local_umax:
                local_umax = sp
    return u, v, float(local_umax)


def velocity_vectorized(psi, row_start, local_n, N):
    h = 1.0 / (N - 1)
    u = np.zeros_like(psi)
    v = np.zeros_like(psi)
    lo, hi = interior_bounds(row_start, local_n, N)
    if lo < hi:
        u[lo:hi, 1:-1] = (psi[lo + 1:hi + 1, 1:-1] - psi[lo - 1:hi - 1, 1:-1]) / (2 * h)
        v[lo:hi, 1:-1] = -(psi[lo:hi, 2:] - psi[lo:hi, :-2]) / (2 * h)
    if row_start + local_n == N:
        u[local_n, :] = 1.0
    return u, v, float(np.max(np.sqrt(u * u + v * v)))


def advance_looped(omega, u, v, args, row_start, local_n, dt):
    N = args.N
    h = 1.0 / (N - 1)
    nu = 1.0 / args.Re
    nxt = omega.copy()
    local_change = 0.0
    lo, hi = interior_bounds(row_start, local_n, N)
    for li in range(lo, hi):
        for j in range(1, N - 1):
            if args.scheme == "central":
                dw_dx = (omega[li, j + 1] - omega[li, j - 1]) / (2 * h)
                dw_dy = (omega[li + 1, j] - omega[li - 1, j]) / (2 * h)
            else:
                dw_dx = (omega[li, j] - omega[li, j - 1]) / h if u[li, j] >= 0 else (omega[li, j + 1] - omega[li, j]) / h
                dw_dy = (omega[li, j] - omega[li - 1, j]) / h if v[li, j] >= 0 else (omega[li + 1, j] - omega[li, j]) / h
            lap = (omega[li + 1, j] + omega[li - 1, j] + omega[li, j + 1] + omega[li, j - 1] - 4.0 * omega[li, j]) / (h * h)
            val = omega[li, j] + dt * (-(u[li, j] * dw_dx + v[li, j] * dw_dy) + nu * lap)
            ch = abs(val - omega[li, j])
            if ch > local_change:
                local_change = ch
            nxt[li, j] = val
    return nxt, float(local_change)


def advance_vectorized(omega, u, v, args, row_start, local_n, dt):
    N = args.N
    h = 1.0 / (N - 1)
    nu = 1.0 / args.Re
    nxt = omega.copy()
    lo, hi = interior_bounds(row_start, local_n, N)
    if lo >= hi:
        return nxt, 0.0
    wc = omega[lo:hi, 1:-1]
    if args.scheme == "central":
        dw_dx = (omega[lo:hi, 2:] - omega[lo:hi, :-2]) / (2 * h)
        dw_dy = (omega[lo + 1:hi + 1, 1:-1] - omega[lo - 1:hi - 1, 1:-1]) / (2 * h)
    else:
        uu = u[lo:hi, 1:-1]
        vv = v[lo:hi, 1:-1]
        dw_dx = np.where(uu >= 0.0, (wc - omega[lo:hi, :-2]) / h, (omega[lo:hi, 2:] - wc) / h)
        dw_dy = np.where(vv >= 0.0, (wc - omega[lo - 1:hi - 1, 1:-1]) / h, (omega[lo + 1:hi + 1, 1:-1] - wc) / h)
    lap = (omega[lo + 1:hi + 1, 1:-1] + omega[lo - 1:hi - 1, 1:-1] + omega[lo:hi, 2:] + omega[lo:hi, :-2] - 4.0 * wc) / (h * h)
    vals = wc + dt * (-(u[lo:hi, 1:-1] * dw_dx + v[lo:hi, 1:-1] * dw_dy) + nu * lap)
    local_change = float(np.max(np.abs(vals - wc)))
    nxt[lo:hi, 1:-1] = vals
    return nxt, local_change

# Numba kernels for the Python hybrid looped style. They are optional and used only when available.
@njit(parallel=True)
def advance_looped_numba(omega, u, v, N, Re, row_start, local_n, dt, central_flag):
    h = 1.0 / (N - 1)
    nu = 1.0 / Re
    nxt = omega.copy()
    changes = np.zeros(local_n + 2)
    lo = 1 + (1 if row_start == 0 else 0)
    hi = local_n + 1 - (1 if row_start + local_n == N else 0)
    for li in prange(lo, hi):
        row_change = 0.0
        for j in range(1, N - 1):
            if central_flag:
                dw_dx = (omega[li, j + 1] - omega[li, j - 1]) / (2 * h)
                dw_dy = (omega[li + 1, j] - omega[li - 1, j]) / (2 * h)
            else:
                dw_dx = (omega[li, j] - omega[li, j - 1]) / h if u[li, j] >= 0 else (omega[li, j + 1] - omega[li, j]) / h
                dw_dy = (omega[li, j] - omega[li - 1, j]) / h if v[li, j] >= 0 else (omega[li + 1, j] - omega[li, j]) / h
            lap = (omega[li + 1, j] + omega[li - 1, j] + omega[li, j + 1] + omega[li, j - 1] - 4.0 * omega[li, j]) / (h * h)
            val = omega[li, j] + dt * (-(u[li, j] * dw_dx + v[li, j] * dw_dy) + nu * lap)
            ch = abs(val - omega[li, j])
            if ch > row_change:
                row_change = ch
            nxt[li, j] = val
        changes[li] = row_change
    return nxt, float(np.max(changes))


def gather_owned(local, local_n, N, comm):
    rank = comm.rank
    size = comm.size
    send = np.ascontiguousarray(local[1:local_n + 1, :])
    counts = None
    displs = None
    recv = None
    if rank == 0:
        counts = np.array([(N // size + (1 if r < N % size else 0)) * N for r in range(size)], dtype=np.int32)
        displs = np.concatenate(([0], np.cumsum(counts[:-1]))).astype(np.int32)
        recv = np.empty((N, N), dtype=np.float64)
    comm.Gatherv(send, (recv, counts, displs, MPI.DOUBLE), root=0)
    return recv


def main():
    comm = MPI.COMM_WORLD
    rank = comm.rank
    size = comm.size
    args = parse_args()
    if args.N < 8:
        raise ValueError("N must be at least 8")
    if args.N < size:
        raise ValueError("N must be at least the number of MPI ranks")
    if HYBRID and NUMBA_AVAILABLE:
        set_num_threads(max(1, args.threads))
    N = args.N
    row_start, local_n, below, above = decomp(N, rank, size)
    psi = np.zeros((local_n + 2, N), dtype=np.float64)
    omega = np.zeros_like(psi)
    h = 1.0 / (N - 1)
    dt_diff = 0.25 * h * h / (1.0 / args.Re)
    dt = min(args.max_dt, dt_diff)
    if rank == 0:
        os.makedirs(args.out_dir, exist_ok=True)
    comm.Barrier()
    t0 = time.time()
    omega_change = np.inf
    psi_change = np.inf
    umax = 0.0
    steps_done = 0
    for step in range(1, args.steps + 1):
        exchange(omega, below, above, comm)
        apply_psi_bc(psi, row_start, local_n, N)
        apply_omega_bc(omega, psi, row_start, local_n, N)
        if KERNEL_STYLE == "vectorized":
            psi, psi_change = solve_poisson_vectorized(psi, omega, args, row_start, local_n, below, above, comm)
        else:
            psi, psi_change = solve_poisson_looped(psi, omega, args, row_start, local_n, below, above, comm)
        exchange(psi, below, above, comm)
        if KERNEL_STYLE == "vectorized":
            u, v, local_umax = velocity_vectorized(psi, row_start, local_n, N)
        else:
            u, v, local_umax = velocity_looped(psi, row_start, local_n, N)
        umax = comm.allreduce(local_umax, op=MPI.MAX)
        dt = min(args.max_dt, args.cfl * h / max(umax, 1e-10), dt_diff)
        if KERNEL_STYLE == "vectorized":
            omega_new, local_change = advance_vectorized(omega, u, v, args, row_start, local_n, dt)
        elif HYBRID and NUMBA_AVAILABLE:
            omega_new, local_change = advance_looped_numba(omega, u, v, N, args.Re, row_start, local_n, dt, args.scheme == "central")
        else:
            omega_new, local_change = advance_looped(omega, u, v, args, row_start, local_n, dt)
        omega_change = comm.allreduce(local_change, op=MPI.MAX)
        omega = omega_new
        steps_done = step
        if omega_change < 1e-8 and psi_change < args.poisson_tol:
            break
    runtime = time.time() - t0
    threads = get_num_threads() if HYBRID else 1
    if rank == 0:
        path = os.path.join(args.out_dir, f"{IMPLEMENTATION}_summary.csv")
        with open(path, "w", encoding="utf-8") as f:
            f.write("Implementation,N,Re,Scheme,Steps,PoissonIters,MPIRanks,ThreadsPerRank,KernelStyle,Runtime_s,FinalOmegaChange,FinalPsiChange,MaxVelocity\n")
            f.write(f"{IMPLEMENTATION},{N},{args.Re},{args.scheme},{steps_done},{args.poisson_iters},{size},{threads},{KERNEL_STYLE},{runtime:.10f},{omega_change:.10e},{psi_change:.10e},{umax:.10e}\n")
    if not args.no_fields:
        gpsi = gather_owned(psi, local_n, N, comm)
        gomega = gather_owned(omega, local_n, N, comm)
        gu = gather_owned(u, local_n, N, comm)
        gv = gather_owned(v, local_n, N, comm)
        if rank == 0:
            path = os.path.join(args.out_dir, f"{IMPLEMENTATION}_N{N}_Re{args.Re}_{args.scheme}_fields.csv")
            with open(path, "w", encoding="utf-8") as f:
                f.write("i,j,x,y,psi,omega,u,v,speed\n")
                for i in range(N):
                    for j in range(N):
                        sp = (gu[i, j] ** 2 + gv[i, j] ** 2) ** 0.5
                        f.write(f"{i},{j},{j*h:.10f},{i*h:.10f},{gpsi[i,j]:.10e},{gomega[i,j]:.10e},{gu[i,j]:.10e},{gv[i,j]:.10e},{sp:.10e}\n")


if __name__ == "__main__":
    main()
