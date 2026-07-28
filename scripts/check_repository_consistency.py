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


def path_in_scope(relative: str, prefix: str | None, exclude_prefixes: list[str]) -> bool:
    if prefix and not (relative == prefix or relative.startswith(prefix.rstrip("/") + "/")):
        return False
    return not any(
        relative == excluded or relative.startswith(excluded.rstrip("/") + "/")
        for excluded in exclude_prefixes
    )


def check_cache(prefix: str | None, exclude_prefixes: list[str]) -> list[str]:
    try:
        tracked = tracked_files()
    except (OSError, subprocess.CalledProcessError) as error:
        return [f"could not inspect tracked files: {error}"]

    errors = []
    for relative in tracked:
        if not path_in_scope(relative, prefix, exclude_prefixes):
            continue
        path = Path(relative)
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            errors.append(f"tracked Python cache artifact: {relative}")
    return errors


def check_backup(prefix: str | None, exclude_prefixes: list[str]) -> list[str]:
    try:
        tracked = tracked_files()
    except (OSError, subprocess.CalledProcessError) as error:
        return [f"could not inspect tracked files: {error}"]

    errors = []
    for relative in tracked:
        if not path_in_scope(relative, prefix, exclude_prefixes):
            continue
        path = Path(relative)
        if path.suffix == ".bak" or ".bak_" in path.name:
            errors.append(f"tracked backup artifact: {relative}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check repository structure without running CFD cases.")
    parser.add_argument(
        "--check",
        choices=["all", "structure", "shell", "python", "cache", "backup"],
        default="all",
        help="Run one category or all checks.",
    )
    parser.add_argument("--path-prefix", help="Limit cache or backup checks to a repository path prefix.")
    parser.add_argument(
        "--exclude-prefix",
        action="append",
        default=[],
        help="Exclude a repository path prefix; may be supplied more than once.",
    )
    args = parser.parse_args()

    checks = {
        "structure": check_structure,
        "shell": check_shell,
        "python": check_python,
        "cache": lambda: check_cache(args.path_prefix, args.exclude_prefix),
        "backup": lambda: check_backup(args.path_prefix, args.exclude_prefix),
    }
    selected = list(checks) if args.check == "all" else [args.check]

    errors = []
    for name in selected:
        category_errors = checks[name]()
        if category_errors:
            errors.extend(f"[{name}] {error}" for error in category_errors)
        else:
            scope = f" ({args.path_prefix})" if args.path_prefix else ""
            print(f"Repository consistency category passed: {name}{scope}")

    if errors:
        print("Repository consistency check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Repository consistency check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
