#!/usr/bin/env python3
"""Create a source-only archive for running the paper benchmark on Stromboli.

The archive intentionally excludes Git metadata, generated results, build outputs,
virtual environments, caches, and previously created distribution archives.
It can therefore be copied to Stromboli with scp and extracted without using Git
on the cluster.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

EXCLUDED_DIR_NAMES = {
    ".git",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "bin",
    "build",
    "dist",
    "node_modules",
}

EXCLUDED_SUFFIXES = {
    ".o",
    ".obj",
    ".so",
    ".dll",
    ".dylib",
    ".exe",
    ".pyc",
    ".pyo",
    ".log",
}

# Generated result trees can be very large and are not needed to launch a clean run.
EXCLUDED_PATH_PARTS = {
    ("comparison", "results"),
    ("comparison", "figures"),
    ("c", "serial", "results"),
    ("c", "openmp", "results"),
    ("c", "mpi", "results"),
    ("cpp", "serial", "results"),
    ("cpp", "openmp", "results"),
    ("cpp", "mpi", "results"),
    ("python", "serial", "results"),
    ("python", "mpi", "results"),
    ("matlab", "results"),
    ("cuda", "results"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package the current checkout for no-Git deployment to Stromboli."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the parent of scripts/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output .tar.gz path. Defaults to dist/lidcavity-paper-snapshot-<UTC timestamp>.tar.gz.",
    )
    return parser.parse_args()


def path_starts_with(parts: tuple[str, ...], prefix: tuple[str, ...]) -> bool:
    return len(parts) >= len(prefix) and parts[: len(prefix)] == prefix


def should_exclude(relative_path: Path) -> bool:
    parts = relative_path.parts
    if any(part in EXCLUDED_DIR_NAMES for part in parts):
        return True
    if relative_path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    if relative_path.name.endswith((".tar.gz", ".tgz", ".zip")):
        return True
    return any(path_starts_with(parts, prefix) for prefix in EXCLUDED_PATH_PARTS)


def iter_source_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if should_exclude(relative):
            continue
        yield path


def optional_git_commit(root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if not (root / "README.md").is_file():
        raise SystemExit(f"Repository root not recognised: {root}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = (
        args.output.resolve()
        if args.output is not None
        else (root / "dist" / f"lidcavity-paper-snapshot-{timestamp}.tar.gz")
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    files = sorted(iter_source_files(root), key=lambda path: path.as_posix())
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "archive_format": "tar.gz",
        "source_root_name": root.name,
        "source_commit": optional_git_commit(root),
        "file_count": len(files),
        "deployment_policy": "No Git operations are required or expected on Stromboli.",
    }

    archive_root = "LidCavity_Paper"
    with tarfile.open(output, mode="w:gz", format=tarfile.PAX_FORMAT) as archive:
        for path in files:
            relative = path.relative_to(root)
            archive.add(path, arcname=str(Path(archive_root) / relative), recursive=False)

        manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
        info = tarfile.TarInfo(name=f"{archive_root}/SNAPSHOT_MANIFEST.json")
        info.size = len(manifest_bytes)
        info.mtime = int(datetime.now(timezone.utc).timestamp())
        info.mode = 0o644
        import io

        archive.addfile(info, io.BytesIO(manifest_bytes))

    digest = sha256_file(output)
    checksum_path = output.with_suffix(output.suffix + ".sha256")
    checksum_path.write_text(f"{digest}  {output.name}\n", encoding="utf-8")

    print(f"Created: {output}")
    print(f"Checksum: {checksum_path}")
    print(f"Files: {len(files)}")
    print("Copy both files to Stromboli with scp; no Git is needed there.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
