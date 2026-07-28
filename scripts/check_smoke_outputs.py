#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def find_summaries(group: Path) -> list[Path]:
    candidates = []
    candidates.extend(sorted((group / "results" / "data").glob("study_summary_*.csv")))
    candidates.extend(sorted((group / "results").glob("study_summary_*.csv")))
    return [path for path in candidates if path.is_file() and path.stat().st_size > 0]


def readable_rows(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as file:
        return sum(1 for _ in csv.DictReader(file))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify that smoke-test solver groups produced readable summaries.")
    parser.add_argument("groups", nargs="+", help="Implementation directories to check.")
    args = parser.parse_args()

    errors = []
    for raw_group in args.groups:
        group = Path(raw_group)
        summaries = find_summaries(group)
        if not summaries:
            errors.append(f"{group}: no non-empty study summary was generated")
            continue

        rows = sum(readable_rows(summary) for summary in summaries)
        if rows < 1:
            errors.append(f"{group}: summary files contain no data rows")
            continue

        print(f"Verified {group}: {len(summaries)} summary file(s), {rows} row(s).")

    if errors:
        print("Smoke output verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
