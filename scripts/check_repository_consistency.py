#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "Makefile",
    "docs/BENCHMARK_TRACKS.md",
    "docs/CURRENT_BENCHMARK_RESULTS.md",
    "docs/PROJECT_OVERVIEW.md",
    "docs/IMPLEMENTATION_LAYOUT.md",
    "docs/RESULTS_GUIDE.md",
    "docs/RUNNING_ON_HPC.md",
    "results/selected/README.md",
    "results/selected/highlights.csv",
    "scripts/generate_selected_results.py",
]

DOMAIN_SOLVER_DIRS = [
    "src/c/openmp_domain_looped",
    "src/c/openmp_domain_vectorized",
    "src/c/mpi_domain_looped",
    "src/c/mpi_domain_vectorized",
    "src/c/hybrid_mpi_openmp_looped",
    "src/c/hybrid_mpi_openmp_vectorized",
    "src/cpp/openmp_domain_looped",
    "src/cpp/openmp_domain_vectorized",
    "src/cpp/mpi_domain_looped",
    "src/cpp/mpi_domain_vectorized",
    "src/cpp/hybrid_mpi_openmp_looped",
    "src/cpp/hybrid_mpi_openmp_vectorized",
    "src/python/mpi_domain_looped",
    "src/python/mpi_domain_vectorized",
    "src/python/hybrid_mpi_openmp_looped",
    "src/python/hybrid_mpi_openmp_vectorized",
]

ACTIVE_SHELL_SCRIPTS = [
    "scripts/run_smoke_cpu.sh",
    "scripts/run_domain_solver_benchmark.sh",
    "scripts/run_strong_scaling_all.sh",
    "scripts/run_openmp_looped_vectorized_scaling.sh",
    "scripts/run_domain_kernel_matrix.sh",
    "scripts/run_all_domain_solvers.sh",
    "scripts/run_domain_decomposition_solvers.sh",
    "scripts/run_mpi_domain.sh",
    "scripts/run_hybrid_mpi_openmp.sh",
]

CRITICAL_PYTHON_SCRIPTS = [
    "scripts/check_repository_consistency.py",
    "scripts/check_smoke_outputs.py",
    "scripts/generate_selected_results.py",
    "scripts/compute_strong_scaling.py",
    "scripts/compare_domain_kernel_matrix.py",
    "scripts/run_parallel_scaling.py",
]

FORBIDDEN_PREFIXES = [
    "c/mpi/",
    "cpp/mpi/",
    "python/mpi/",
    "jobs/",
    "comparison/results/final/",
    "comparison/results/final_clean/",
]

FORBIDDEN_PATHS = {
    "comparison/results/raw/c_mpi_r8_full.csv",
    "comparison/results/raw/cpp_mpi_r8_full.csv",
    "README_ONE_COMMAND.md",
    "README_RUN_ON_STROMBOLI.md",
    "RUN_EVERYTHING_ON_STROMBOLI.sh",
    "01_prepare_stromboli.sh",
    "03_submit_all.sh",
    "scripts/submit_stromboli_full_data_first_no_cuda.sh",
}

TEXT_SUFFIXES = {".md", ".txt", ".py", ".sh", ".yml", ".yaml"}
FORBIDDEN_TEXT = [
    "python/mpi/",
    "c/mpi/",
    "cpp/mpi/",
    "c_mpi,cpp_mpi,python_mpi",
]


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=True
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def read_text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8", errors="replace")


def main() -> int:
    errors: list[str] = []

    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    for directory in DOMAIN_SOLVER_DIRS:
        if not (ROOT / directory / "Makefile").is_file():
            errors.append(f"missing domain Makefile: {directory}/Makefile")

    for relative in ACTIVE_SHELL_SCRIPTS:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing shell script: {relative}")
            continue
        script_bytes = path.read_bytes().replace(b"\r\n", b"\n")
        check = subprocess.run(
            ["bash", "-n", "-s"],
            input=script_bytes,
            capture_output=True,
        )
        if check.returncode:
            stderr = check.stderr.decode("utf-8", errors="replace").strip()
            errors.append(f"shell syntax error in {relative}: {stderr}")

    for relative in CRITICAL_PYTHON_SCRIPTS:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing Python script: {relative}")
            continue
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as error:
            errors.append(f"Python syntax error in {relative}: {error}")

    try:
        tracked = tracked_files()
    except (OSError, subprocess.CalledProcessError) as error:
        errors.append(f"could not inspect tracked files: {error}")
        tracked = []

    for relative in tracked:
        path = Path(relative)
        if any(relative.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            errors.append(f"removed case-parallel/generated path is still tracked: {relative}")
        if relative in FORBIDDEN_PATHS:
            errors.append(f"obsolete workflow path is still tracked: {relative}")
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            errors.append(f"tracked Python cache: {relative}")
        if path.suffix == ".bak" or ".bak_" in path.name:
            errors.append(f"tracked backup file: {relative}")

        if relative == "scripts/check_repository_consistency.py":
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES or not (ROOT / relative).is_file():
            continue
        text = read_text(relative)
        for token in FORBIDDEN_TEXT:
            if token in text:
                errors.append(f"obsolete case-parallel reference in {relative}: {token}")

    for relative in [
        "src/c/mpi_domain_looped/Makefile",
        "src/c/mpi_domain_vectorized/Makefile",
        "src/c/hybrid_mpi_openmp_looped/Makefile",
        "src/c/hybrid_mpi_openmp_vectorized/Makefile",
    ]:
        if (ROOT / relative).is_file() and "CC = mpicc" not in read_text(relative):
            errors.append(f"C spatial-MPI Makefile must force the MPI wrapper: {relative}")

    if errors:
        print("Repository consistency check failed:")
        for error in sorted(set(errors)):
            print(f"- {error}")
        return 1

    print("Repository consistency check passed.")
    print(f"Checked {len(tracked)} tracked files and {len(DOMAIN_SOLVER_DIRS)} domain implementations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
