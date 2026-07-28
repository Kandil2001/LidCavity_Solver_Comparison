#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    "README.md",
    "docs/BENCHMARK_TRACKS.md",
    "docs/CURRENT_BENCHMARK_RESULTS.md",
    "docs/PROJECT_OVERVIEW.md",
    "docs/IMPLEMENTATION_LAYOUT.md",
    "docs/RESULTS_GUIDE.md",
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
    "scripts/run_strong_scaling_all.sh",
    "scripts/run_openmp_looped_vectorized_scaling.sh",
    "scripts/run_domain_kernel_matrix.sh",
    "scripts/run_all_domain_solvers.sh",
    "scripts/run_domain_decomposition_solvers.sh",
    "scripts/run_mpi_domain.sh",
    "scripts/run_hybrid_mpi_openmp.sh",
]

CRITICAL_PYTHON_SCRIPTS = [
    "scripts/compute_strong_scaling.py",
    "scripts/compare_domain_kernel_matrix.py",
    "scripts/check_repository_consistency.py",
]

LEGACY_DOMAIN_TOKENS = [
    "c/openmp_domain_",
    "c/mpi_domain_",
    "c/hybrid_mpi_openmp_",
    "cpp/openmp_domain_",
    "cpp/mpi_domain_",
    "cpp/hybrid_mpi_openmp_",
    "python/mpi_domain_",
    "python/hybrid_mpi_openmp_",
]


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def check_structure() -> list[str]:
    errors = []
    for relative in REQUIRED_DOCS:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required documentation: {relative}")
    for relative in DOMAIN_SOLVER_DIRS:
        if not (ROOT / relative / "Makefile").is_file():
            errors.append(f"missing organized domain solver Makefile: {relative}/Makefile")
    return errors


def check_shell() -> list[str]:
    errors = []
    for relative in ACTIVE_SHELL_SCRIPTS:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing active shell script: {relative}")
            continue
        syntax = subprocess.run(["bash", "-n", str(path)], text=True, capture_output=True)
        if syntax.returncode != 0:
            errors.append(f"shell syntax error in {relative}: {syntax.stderr.strip()}")

        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not any(token in line for token in LEGACY_DOMAIN_TOKENS):
                continue
            if "src/" not in line and "SRC_ROOT" not in line:
                errors.append(f"legacy pre-src domain path in {relative}:{line_number}: {line.strip()}")
    return errors


def check_python() -> list[str]:
    errors = []
    for relative in CRITICAL_PYTHON_SCRIPTS:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing critical Python script: {relative}")
            continue
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as error:
            errors.append(f"Python syntax error in {relative}: {error}")
    return errors


def check_artifacts() -> list[str]:
    errors = []
    try:
        tracked = tracked_files()
    except (OSError, subprocess.CalledProcessError) as error:
        return [f"could not inspect tracked files: {error}"]

    for relative in tracked:
        path = Path(relative)
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            errors.append(f"tracked Python cache artifact: {relative}")
        if path.suffix == ".bak" or ".bak_" in path.name:
            errors.append(f"tracked backup artifact: {relative}")
    return errors


CHECKS = {
    "structure": check_structure,
    "shell": check_shell,
    "python": check_python,
    "artifacts": check_artifacts,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check repository structure without running CFD cases.")
    parser.add_argument(
        "--check",
        choices=["all", *CHECKS],
        default="all",
        help="Run one category or all checks.",
    )
    args = parser.parse_args()

    selected = list(CHECKS) if args.check == "all" else [args.check]
    errors = []
    for name in selected:
        category_errors = CHECKS[name]()
        if category_errors:
            errors.extend(f"[{name}] {error}" for error in category_errors)
        else:
            print(f"Repository consistency category passed: {name}")

    if errors:
        print("Repository consistency check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Repository consistency check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
