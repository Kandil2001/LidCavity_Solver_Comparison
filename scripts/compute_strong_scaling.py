#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, math, statistics
from pathlib import Path
from collections import defaultdict


def fnum(x):
    try:
        if x in (None, ''):
            return None
        return float(x)
    except Exception:
        return None


def read_rows(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    fields = list(rows[0].keys())
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def median(values):
    return statistics.median(values) if values else None


def mean(values):
    return statistics.mean(values) if values else None


def main() -> int:
    p = argparse.ArgumentParser(description='Compute strong-scaling speedup and efficiency from raw timing rows.')
    p.add_argument('--raw', default='comparison/results/strong_scaling/strong_scaling_raw.csv')
    p.add_argument('--out-dir', default='comparison/results/strong_scaling')
    p.add_argument('--plots', action='store_true', help='Write matplotlib PNG plots if matplotlib is available')
    args = p.parse_args()

    raw_path = Path(args.raw)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = read_rows(raw_path)
    success = [r for r in raw if r.get('status') == 'success' and fnum(r.get('runtime_s')) is not None]

    grouped = defaultdict(list)
    for r in success:
        key = (
            r['case_id'], r['solver_group'], r['language'], r['parallel_model'], r['kernel_style'],
            int(float(r['total_cores'])), int(float(r['mpi_ranks'])), int(float(r['threads_per_rank'])),
            r.get('N',''), r.get('Re',''), r.get('scheme',''), r.get('pressure',''), r.get('steps',''), r.get('poisson_iters','')
        )
        grouped[key].append(fnum(r['runtime_s']))

    summary = []
    for key, vals in sorted(grouped.items()):
        (case_id, solver, lang, par, kernel, cores, ranks, threads, N, Re, scheme, pressure, steps, poisson_iters) = key
        vals = [v for v in vals if v is not None]
        summary.append({
            'case_id': case_id,
            'solver_group': solver,
            'language': lang,
            'parallel_model': par,
            'kernel_style': kernel,
            'N': N,
            'Re': Re,
            'scheme': scheme,
            'pressure': pressure,
            'steps': steps,
            'poisson_iters': poisson_iters,
            'total_cores': cores,
            'mpi_ranks': ranks,
            'threads_per_rank': threads,
            'runs': len(vals),
            'runtime_min_s': f'{min(vals):.10g}',
            'runtime_mean_s': f'{mean(vals):.10g}',
            'runtime_median_s': f'{median(vals):.10g}',
        })

    # Baseline is the smallest core count for each exact solver and case.
    base = {}
    for r in summary:
        key = (r['case_id'], r['solver_group'], r.get('pressure',''))
        cores = int(r['total_cores'])
        runtime = fnum(r['runtime_median_s'])
        if runtime is None:
            continue
        if key not in base or cores < base[key][0]:
            base[key] = (cores, runtime)

    for r in summary:
        key = (r['case_id'], r['solver_group'], r.get('pressure',''))
        runtime = fnum(r['runtime_median_s'])
        cores = int(r['total_cores'])
        if key in base and runtime:
            base_cores, base_runtime = base[key]
            speedup = base_runtime / runtime
            # Strong-scaling efficiency normalized by core ratio from the baseline.
            ideal_core_ratio = cores / base_cores
            eff = speedup / ideal_core_ratio
            r['baseline_cores'] = base_cores
            r['baseline_runtime_s'] = f'{base_runtime:.10g}'
            r['speedup_vs_baseline'] = f'{speedup:.6g}'
            r['parallel_efficiency'] = f'{eff:.6g}'
        else:
            r['baseline_cores'] = ''
            r['baseline_runtime_s'] = ''
            r['speedup_vs_baseline'] = ''
            r['parallel_efficiency'] = ''

    write_csv(out_dir / 'strong_scaling_summary.csv', summary)

    # Compact best runtime table by case/solver.
    best = []
    best_groups = defaultdict(list)
    for r in summary:
        best_groups[(r['case_id'], r['solver_group'], r.get('pressure',''))].append(r)
    for key, vals in sorted(best_groups.items()):
        vals = sorted(vals, key=lambda x: fnum(x['runtime_median_s']) if fnum(x['runtime_median_s']) is not None else 1e99)
        b = vals[0].copy()
        b['best_total_cores'] = b['total_cores']
        b['best_runtime_median_s'] = b['runtime_median_s']
        best.append(b)
    write_csv(out_dir / 'strong_scaling_best_by_solver.csv', best)

    # Markdown report.
    lines = []
    lines.append('# Strong Scaling Study Report')
    lines.append('')
    lines.append('Generated by `scripts/compute_strong_scaling.py`.')
    lines.append('')
    lines.append('## What was measured')
    lines.append('')
    lines.append('- Pure MPI domain-decomposition solvers: core count = MPI ranks.')
    lines.append('- Hybrid MPI/shared-memory solvers: core count = MPI ranks × threads per rank.')
    lines.append('- OpenMP solvers: core count = OpenMP threads.')
    lines.append('- Speedup is computed against the smallest available core count for the same solver and same case.')
    lines.append('- Efficiency is speedup divided by the ideal core-count ratio.')
    lines.append('')
    if not summary:
        lines.append('No successful timing rows found yet. Run `bash scripts/run_strong_scaling_all.sh` first.')
    else:
        by_case = defaultdict(list)
        for r in summary:
            by_case[r['case_id']].append(r)
        for case_id in sorted(by_case):
            rows = sorted(by_case[case_id], key=lambda r: (r['solver_group'], int(r['total_cores'])))
            lines.append(f'## Case `{case_id}`')
            if rows:
                first = rows[0]
                lines.append(f"N={first['N']}, Re={first['Re']}, scheme={first['scheme']}, pressure={first['pressure']}, steps={first['steps']}, poisson_iters={first['poisson_iters']}")
            lines.append('')
            lines.append('| Solver | Model | Kernel | Cores | Ranks | Threads/rank | Runtime median [s] | Speedup | Efficiency | Runs |')
            lines.append('|---|---|---|---:|---:|---:|---:|---:|---:|---:|')
            for r in rows:
                lines.append(f"| `{r['solver_group']}` | {r['parallel_model']} | {r['kernel_style']} | {r['total_cores']} | {r['mpi_ranks']} | {r['threads_per_rank']} | {r['runtime_median_s']} | {r['speedup_vs_baseline']} | {r['parallel_efficiency']} | {r['runs']} |")
            lines.append('')
        lines.append('## Output files')
        lines.append('')
        lines.append('- `strong_scaling_raw.csv`: every individual run.')
        lines.append('- `strong_scaling_summary.csv`: median/min/mean runtime, speedup, and efficiency.')
        lines.append('- `strong_scaling_best_by_solver.csv`: best core count and runtime per solver/case.')
    (out_dir / 'strong_scaling_report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    if args.plots and summary:
        try:
            import matplotlib.pyplot as plt
            plot_dir = out_dir / 'figures'
            plot_dir.mkdir(parents=True, exist_ok=True)
            by_case_solver = defaultdict(list)
            for r in summary:
                by_case_solver[(r['case_id'], r['solver_group'])].append(r)
            for metric, ylabel, fname in [
                ('runtime_median_s', 'Median runtime [s]', 'runtime'),
                ('speedup_vs_baseline', 'Speedup [-]', 'speedup'),
                ('parallel_efficiency', 'Parallel efficiency [-]', 'efficiency'),
            ]:
                for case_id in sorted({r['case_id'] for r in summary}):
                    plt.figure(figsize=(12, 7))
                    for (cid, solver), rows in sorted(by_case_solver.items()):
                        if cid != case_id:
                            continue
                        rows = sorted(rows, key=lambda x: int(x['total_cores']))
                        xs = [int(r['total_cores']) for r in rows]
                        ys = [fnum(r[metric]) for r in rows]
                        if any(y is not None for y in ys):
                            plt.plot(xs, ys, marker='o', label=solver)
                    plt.xlabel('Total cores / ranks')
                    plt.ylabel(ylabel)
                    plt.title(f'Strong scaling {metric} - {case_id}')
                    plt.grid(True, alpha=0.3)
                    plt.legend(fontsize=7, ncol=2)
                    plt.tight_layout()
                    plt.savefig(plot_dir / f'{fname}_{case_id}.png', dpi=180)
                    plt.close()
        except Exception as e:
            print(f'Plotting skipped: {e}')

    print(f"Wrote {out_dir / 'strong_scaling_summary.csv'}")
    print(f"Wrote {out_dir / 'strong_scaling_report.md'}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
