#!/usr/bin/env python3
from __future__ import annotations

import csv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / os.environ.get("SRC_ROOT", "src")
OUT = ROOT / "comparison" / "results" / "domain_kernel_matrix"
OUT.mkdir(parents=True, exist_ok=True)


def entry(name: str, language: str, parallel: str, kernel: str, rel_dir: str, summary: str):
    rel = Path(os.environ.get("SRC_ROOT", "src")) / rel_dir / "results" / "data" / summary
    return name, language, parallel, kernel, rel.as_posix()


ENTRIES = [
    entry("c_mpi_domain_looped", "c", "mpi", "looped", "c/mpi_domain_looped", "c_mpi_domain_looped_summary.csv"),
    entry("c_mpi_domain_vectorized", "c", "mpi", "vectorized", "c/mpi_domain_vectorized", "c_mpi_domain_vectorized_summary.csv"),
    entry("c_hybrid_mpi_openmp_looped", "c", "hybrid", "looped", "c/hybrid_mpi_openmp_looped", "c_hybrid_mpi_openmp_looped_summary.csv"),
    entry("c_hybrid_mpi_openmp_vectorized", "c", "hybrid", "vectorized", "c/hybrid_mpi_openmp_vectorized", "c_hybrid_mpi_openmp_vectorized_summary.csv"),
    entry("cpp_mpi_domain_looped", "cpp", "mpi", "looped", "cpp/mpi_domain_looped", "cpp_mpi_domain_looped_summary.csv"),
    entry("cpp_mpi_domain_vectorized", "cpp", "mpi", "vectorized", "cpp/mpi_domain_vectorized", "cpp_mpi_domain_vectorized_summary.csv"),
    entry("cpp_hybrid_mpi_openmp_looped", "cpp", "hybrid", "looped", "cpp/hybrid_mpi_openmp_looped", "cpp_hybrid_mpi_openmp_looped_summary.csv"),
    entry("cpp_hybrid_mpi_openmp_vectorized", "cpp", "hybrid", "vectorized", "cpp/hybrid_mpi_openmp_vectorized", "cpp_hybrid_mpi_openmp_vectorized_summary.csv"),
    entry("python_mpi_domain_looped", "python", "mpi", "looped", "python/mpi_domain_looped", "python_mpi_domain_looped_summary.csv"),
    entry("python_mpi_domain_vectorized", "python", "mpi", "vectorized", "python/mpi_domain_vectorized", "python_mpi_domain_vectorized_summary.csv"),
    entry("python_hybrid_mpi_threaded_looped", "python", "hybrid", "looped", "python/hybrid_mpi_openmp_looped", "python_hybrid_mpi_threaded_looped_summary.csv"),
    entry("python_hybrid_mpi_threaded_vectorized", "python", "hybrid", "vectorized", "python/hybrid_mpi_openmp_vectorized", "python_hybrid_mpi_threaded_vectorized_summary.csv"),
]


def read_csv(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def pick(row, *names, default=""):
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return default


def fnum(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def inum(value, default=1):
    number = fnum(value)
    return int(number) if number is not None else default


rows = []
missing = []
for implementation, language, parallel, kernel, relative_path in ENTRIES:
    source = ROOT / relative_path
    source_rows = read_csv(source)
    if not source_rows:
        missing.append(relative_path)
    for raw in source_rows:
        runtime = fnum(pick(raw, "Runtime_s", "runtime_s"))
        ranks = inum(pick(raw, "MPIRanks", "MPI_Ranks", "mpi_ranks"), default=1)
        threads = inum(
            pick(raw, "OpenMPThreads", "OpenMP_Threads", "ThreadsPerRank", "threads_per_rank"),
            default=1,
        )
        rows.append(
            {
                "numerical_track": "streamfunction_vorticity_domain",
                "execution_status": "completed",
                "solver_group": implementation,
                "language": language,
                "parallel_type": "mpi_domain" if parallel == "mpi" else "hybrid_mpi_shared_memory",
                "kernel_style": kernel,
                "N": pick(raw, "N"),
                "Re": pick(raw, "Re"),
                "scheme": pick(raw, "Scheme", "scheme"),
                "pressure_solver": pick(raw, "PoissonSolver", "PressureSolver", "pressure", default="unknown"),
                "sor_omega": pick(raw, "SOROmega", "sor_omega"),
                "steps": pick(raw, "Steps", "steps"),
                "poisson_iters": pick(raw, "PoissonIters", "poisson_iters"),
                "mpi_ranks": str(ranks),
                "threads_per_rank": str(threads),
                "total_cores": str(ranks * threads),
                "runtime_s": f"{runtime:.10f}" if runtime is not None else "",
                "summary_file": relative_path,
            }
        )


def comparison_key(row, kernel_style=None, parallel_type=None):
    return (
        row["language"],
        parallel_type or row["parallel_type"],
        kernel_style or row["kernel_style"],
        row["N"],
        row["Re"],
        row["scheme"],
        row["pressure_solver"],
        row["steps"],
        row["poisson_iters"],
        row["total_cores"],
    )


lookup = {comparison_key(row): fnum(row["runtime_s"]) for row in rows}
for row in rows:
    runtime = fnum(row["runtime_s"])
    loop_runtime = lookup.get(comparison_key(row, kernel_style="looped"))
    mpi_runtime = lookup.get(comparison_key(row, parallel_type="mpi_domain"))

    row["speedup_vs_looped_same_configuration"] = ""
    if runtime and loop_runtime and row["kernel_style"] == "vectorized":
        row["speedup_vs_looped_same_configuration"] = f"{loop_runtime / runtime:.6g}"

    row["hybrid_speedup_vs_mpi_same_configuration"] = ""
    if runtime and mpi_runtime and row["parallel_type"] == "hybrid_mpi_shared_memory":
        row["hybrid_speedup_vs_mpi_same_configuration"] = f"{mpi_runtime / runtime:.6g}"

out_csv = OUT / "domain_kernel_matrix_times.csv"
if rows:
    with out_csv.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
else:
    out_csv.write_text("", encoding="utf-8")

report = OUT / "domain_kernel_matrix_report.md"
lines = [
    "# Domain-decomposition kernel matrix report",
    "",
    "Generated by `scripts/compare_domain_kernel_matrix.py`.",
    "",
    "This report covers only the organized streamfunction–vorticity domain-scaling track under `src/`.",
    "",
    "## Solver matrix",
    "",
    "| Language | MPI looped | MPI vectorized | Hybrid looped | Hybrid vectorized |",
    "|---|---|---|---|---|",
    "| C | `src/c/mpi_domain_looped` | `src/c/mpi_domain_vectorized` | `src/c/hybrid_mpi_openmp_looped` | `src/c/hybrid_mpi_openmp_vectorized` |",
    "| C++ | `src/cpp/mpi_domain_looped` | `src/cpp/mpi_domain_vectorized` | `src/cpp/hybrid_mpi_openmp_looped` | `src/cpp/hybrid_mpi_openmp_vectorized` |",
    "| Python | `src/python/mpi_domain_looped` | `src/python/mpi_domain_vectorized` | `src/python/hybrid_mpi_openmp_looped` | `src/python/hybrid_mpi_openmp_vectorized` |",
    "",
    "Compare rows only when the physical case, pressure solver, step count, Poisson-iteration count, and total core count match.",
    "",
]

if missing:
    lines.extend(["## Missing summaries", ""])
    lines.extend(f"- `{path}`" for path in missing)
    lines.append("")

if not rows:
    lines.append("No summary CSVs were found. Run `bash scripts/run_domain_kernel_matrix.sh` first.")
else:
    lines.extend(
        [
            "## Runtime table",
            "",
            "| Solver | N | Re | Scheme | Pressure | Ranks | Threads/rank | Cores | Kernel | Runtime [s] | Vectorized speedup | Hybrid speedup |",
            "|---|---:|---:|---|---|---:|---:|---:|---|---:|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(
            f"| `{row['solver_group']}` | {row['N']} | {row['Re']} | {row['scheme']} | "
            f"{row['pressure_solver']} | {row['mpi_ranks']} | {row['threads_per_rank']} | "
            f"{row['total_cores']} | {row['kernel_style']} | {row['runtime_s']} | "
            f"{row['speedup_vs_looped_same_configuration']} | "
            f"{row['hybrid_speedup_vs_mpi_same_configuration']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "- These are fixed-step execution measurements unless a separate convergence field proves otherwise.",
            "- A completed process is not automatically a converged or validated CFD solution.",
            "- Cross-language comparisons require identical numerical and hardware configurations.",
        ]
    )

report.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Wrote {out_csv}")
print(f"Wrote {report}")
if not rows:
    print("No domain-kernel matrix rows found. Run scripts/run_domain_kernel_matrix.sh first.")
