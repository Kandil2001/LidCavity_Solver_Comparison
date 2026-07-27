#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, os, socket, sys
from datetime import datetime, timezone
from pathlib import Path


def read_first_row(path: Path) -> dict:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    with path.open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    return rows[-1] if rows else {}


def pick(row: dict, *names: str, default: str = '') -> str:
    for name in names:
        value = row.get(name)
        if value not in (None, ''):
            return str(value)
    return default


def main() -> int:
    p = argparse.ArgumentParser(description='Append one solver timing row to the strong-scaling raw CSV.')
    p.add_argument('--summary', required=True)
    p.add_argument('--out-dir', default='comparison/results/strong_scaling')
    p.add_argument('--solver-group', required=True)
    p.add_argument('--language', required=True)
    p.add_argument('--parallel-model', required=True)
    p.add_argument('--kernel-style', required=True)
    p.add_argument('--case-id', required=True)
    p.add_argument('--N', required=True)
    p.add_argument('--Re', required=True)
    p.add_argument('--scheme', required=True)
    p.add_argument('--pressure', default='')
    p.add_argument('--steps', required=True)
    p.add_argument('--poisson-iters', required=True)
    p.add_argument('--mpi-ranks', required=True)
    p.add_argument('--threads-per-rank', required=True)
    p.add_argument('--total-cores', required=True)
    p.add_argument('--repeat', required=True)
    p.add_argument('--status', default='success')
    p.add_argument('--log-file', default='')
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / 'strong_scaling_raw.csv'
    summary_path = Path(args.summary)
    row = read_first_row(summary_path)

    runtime = pick(row, 'Runtime_s', 'runtime_s')
    # For failed commands, keep row but with empty runtime.
    if args.status != 'success':
        runtime = ''

    data = {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'host': socket.gethostname(),
        'solver_group': args.solver_group,
        'language': args.language,
        'parallel_model': args.parallel_model,
        'kernel_style': args.kernel_style,
        'case_id': args.case_id,
        'N': args.N,
        'Re': args.Re,
        'scheme': args.scheme,
        'pressure': args.pressure,
        'steps': args.steps,
        'poisson_iters': args.poisson_iters,
        'mpi_ranks': args.mpi_ranks,
        'threads_per_rank': args.threads_per_rank,
        'total_cores': args.total_cores,
        'repeat': args.repeat,
        'runtime_s': runtime,
        'final_omega_change': pick(row, 'FinalOmegaChange'),
        'final_psi_change': pick(row, 'FinalPsiChange'),
        'final_ru': pick(row, 'FinalRu'),
        'final_rv': pick(row, 'FinalRv'),
        'final_rc_mass': pick(row, 'FinalRcMass'),
        'final_rc_div': pick(row, 'FinalRcDiv'),
        'max_velocity': pick(row, 'MaxVelocity'),
        'source_summary': str(summary_path),
        'status': args.status,
        'log_file': args.log_file,
    }
    fieldnames = list(data.keys())
    exists = out_csv.exists() and out_csv.stat().st_size > 0
    with out_csv.open('a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            w.writeheader()
        w.writerow(data)
    print(f"Appended {args.solver_group} cores={args.total_cores} runtime={runtime or 'NA'} status={args.status}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
