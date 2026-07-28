#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path


def fnum(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def read_rows(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def distribution(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    if len(ordered) == 1:
        q1 = q3 = ordered[0]
        std = 0.0
    else:
        q1, _, q3 = statistics.quantiles(ordered, n=4, method="inclusive")
        std = statistics.stdev(ordered)
    return {
        "min": min(ordered),
        "q1": q1,
        "median": statistics.median(ordered),
        "mean": statistics.mean(ordered),
        "q3": q3,
        "iqr": q3 - q1,
        "std": std,
        "max": max(ordered),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compute fixed-configuration strong-scaling statistics from raw timing rows."
    )
    parser.add_argument("--raw", default="comparison/results/strong_scaling/strong_scaling_raw.csv")
    parser.add_argument("--out-dir", default="comparison/results/strong_scaling")
    parser.add_argument("--plots", action="store_true", help="Write matplotlib plots when available")
    args = parser.parse_args()

    raw_path = Path(args.raw)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    raw = read_rows(raw_path)
    successful = [
        row
        for row in raw
        if row.get("status", "").lower() == "success" and fnum(row.get("runtime_s")) is not None
    ]

    grouped: dict[tuple, list[float]] = defaultdict(list)
    for row in successful:
        key = (
            row.get("case_id", ""),
            row.get("solver_group", ""),
            row.get("language", ""),
            row.get("parallel_model", ""),
            row.get("kernel_style", ""),
            row.get("pressure", "unknown"),
            int(float(row.get("total_cores", 1))),
            int(float(row.get("mpi_ranks", 1))),
            int(float(row.get("threads_per_rank", 1))),
            row.get("N", ""),
            row.get("Re", ""),
            row.get("scheme", ""),
            row.get("steps", ""),
            row.get("poisson_iters", ""),
        )
        runtime = fnum(row.get("runtime_s"))
        if runtime is not None:
            grouped[key].append(runtime)

    summary = []
    for key, values in sorted(grouped.items()):
        (
            case_id,
            solver,
            language,
            parallel_model,
            kernel,
            pressure,
            cores,
            ranks,
            threads,
            n_value,
            re_value,
            scheme,
            steps,
            poisson_iters,
        ) = key
        stats = distribution(values)
        summary.append(
            {
                "case_id": case_id,
                "solver_group": solver,
                "language": language,
                "parallel_model": parallel_model,
                "kernel_style": kernel,
                "pressure": pressure,
                "N": n_value,
                "Re": re_value,
                "scheme": scheme,
                "steps": steps,
                "poisson_iters": poisson_iters,
                "total_cores": cores,
                "mpi_ranks": ranks,
                "threads_per_rank": threads,
                "runs": len(values),
                "runtime_min_s": f"{stats['min']:.10g}",
                "runtime_q1_s": f"{stats['q1']:.10g}",
                "runtime_median_s": f"{stats['median']:.10g}",
                "runtime_mean_s": f"{stats['mean']:.10g}",
                "runtime_q3_s": f"{stats['q3']:.10g}",
                "runtime_iqr_s": f"{stats['iqr']:.10g}",
                "runtime_std_s": f"{stats['std']:.10g}",
                "runtime_max_s": f"{stats['max']:.10g}",
            }
        )

    # Baseline is the smallest core count for the same solver, case, and pressure solver.
    baseline = {}
    for row in summary:
        key = (
            row["case_id"],
            row["solver_group"],
            row["language"],
            row["parallel_model"],
            row["kernel_style"],
            row["pressure"],
        )
        cores = int(row["total_cores"])
        runtime = fnum(row["runtime_median_s"])
        if runtime is None:
            continue
        if key not in baseline or cores < baseline[key][0]:
            baseline[key] = (cores, runtime)

    for row in summary:
        key = (
            row["case_id"],
            row["solver_group"],
            row["language"],
            row["parallel_model"],
            row["kernel_style"],
            row["pressure"],
        )
        runtime = fnum(row["runtime_median_s"])
        cores = int(row["total_cores"])
        if key in baseline and runtime and runtime > 0:
            base_cores, base_runtime = baseline[key]
            speedup = base_runtime / runtime
            ideal_core_ratio = cores / base_cores
            efficiency = speedup / ideal_core_ratio
            row["baseline_cores"] = base_cores
            row["baseline_runtime_s"] = f"{base_runtime:.10g}"
            row["speedup_vs_baseline"] = f"{speedup:.6g}"
            row["parallel_efficiency"] = f"{efficiency:.6g}"
        else:
            row["baseline_cores"] = ""
            row["baseline_runtime_s"] = ""
            row["speedup_vs_baseline"] = ""
            row["parallel_efficiency"] = ""

    write_csv(out_dir / "strong_scaling_summary.csv", summary)

    # Best median runtime is retained per exact solver/case/pressure configuration.
    best = []
    best_groups = defaultdict(list)
    for row in summary:
        key = (
            row["case_id"],
            row["solver_group"],
            row["language"],
            row["parallel_model"],
            row["kernel_style"],
            row["pressure"],
        )
        best_groups[key].append(row)
    for values in best_groups.values():
        ordered = sorted(
            values,
            key=lambda row: fnum(row["runtime_median_s"])
            if fnum(row["runtime_median_s"]) is not None
            else float("inf"),
        )
        selected = ordered[0].copy()
        selected["best_total_cores"] = selected["total_cores"]
        selected["best_runtime_median_s"] = selected["runtime_median_s"]
        best.append(selected)
    write_csv(out_dir / "strong_scaling_best_by_solver.csv", best)

    lines = [
        "# Strong-scaling study report",
        "",
        "Generated by `scripts/compute_strong_scaling.py`.",
        "",
        "## Interpretation",
        "",
        "- Pure MPI domain solvers use MPI ranks as the core count.",
        "- Hybrid solvers use MPI ranks multiplied by threads per rank.",
        "- OpenMP solvers use OpenMP threads as the core count.",
        "- Speedup is calculated from repeated-run median runtime.",
        "- RBGS and RBSOR are kept as separate configurations.",
        "- A successful timing row records process completion, not automatic numerical convergence.",
        "",
    ]

    if not summary:
        lines.append("No successful timing rows were found.")
    else:
        by_case = defaultdict(list)
        for row in summary:
            by_case[row["case_id"]].append(row)
        for case_id in sorted(by_case):
            rows = sorted(
                by_case[case_id],
                key=lambda row: (
                    row["solver_group"],
                    row["pressure"],
                    int(row["total_cores"]),
                ),
            )
            lines.append(f"## Case `{case_id}`")
            if rows:
                first = rows[0]
                lines.append(
                    f"N={first['N']}, Re={first['Re']}, scheme={first['scheme']}, "
                    f"steps={first['steps']}, Poisson iterations={first['poisson_iters']}"
                )
            lines.extend(
                [
                    "",
                    "| Solver | Pressure | Model | Kernel | Cores | Ranks | Threads/rank | Runs | Median [s] | IQR [s] | Speedup | Efficiency |",
                    "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
                ]
            )
            for row in rows:
                lines.append(
                    f"| `{row['solver_group']}` | {row['pressure']} | {row['parallel_model']} | "
                    f"{row['kernel_style']} | {row['total_cores']} | {row['mpi_ranks']} | "
                    f"{row['threads_per_rank']} | {row['runs']} | {row['runtime_median_s']} | "
                    f"{row['runtime_iqr_s']} | {row['speedup_vs_baseline']} | "
                    f"{row['parallel_efficiency']} |"
                )
            lines.append("")

        lines.extend(
            [
                "## Output files",
                "",
                "- `strong_scaling_raw.csv`: every individual execution row.",
                "- `strong_scaling_summary.csv`: fixed-configuration statistics and scaling metrics.",
                "- `strong_scaling_best_by_solver.csv`: best median core count per solver, case, and pressure solver.",
            ]
        )

    (out_dir / "strong_scaling_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    if args.plots and summary:
        try:
            import matplotlib.pyplot as plt

            plot_dir = out_dir / "figures"
            plot_dir.mkdir(parents=True, exist_ok=True)
            by_series = defaultdict(list)
            for row in summary:
                label = f"{row['solver_group']} [{row['pressure']}]"
                by_series[(row["case_id"], label)].append(row)

            for metric, ylabel, filename in [
                ("runtime_median_s", "Median runtime [s]", "runtime"),
                ("speedup_vs_baseline", "Speedup [-]", "speedup"),
                ("parallel_efficiency", "Parallel efficiency [-]", "efficiency"),
            ]:
                for case_id in sorted({row["case_id"] for row in summary}):
                    plt.figure(figsize=(12, 7))
                    for (current_case, label), rows in sorted(by_series.items()):
                        if current_case != case_id:
                            continue
                        ordered = sorted(rows, key=lambda row: int(row["total_cores"]))
                        x_values = [int(row["total_cores"]) for row in ordered]
                        y_values = [fnum(row[metric]) for row in ordered]
                        valid = [(x, y) for x, y in zip(x_values, y_values) if y is not None]
                        if valid:
                            plt.plot(
                                [x for x, _ in valid],
                                [y for _, y in valid],
                                marker="o",
                                label=label,
                            )
                    plt.xlabel("Total cores / ranks")
                    plt.ylabel(ylabel)
                    plt.title(f"Strong scaling: {case_id}")
                    plt.grid(True, alpha=0.3)
                    plt.legend(fontsize=7, ncol=2)
                    plt.tight_layout()
                    plt.savefig(plot_dir / f"{filename}_{case_id}.png", dpi=180)
                    plt.close()
        except Exception as error:
            print(f"Plotting skipped: {error}")

    print(f"Wrote {out_dir / 'strong_scaling_summary.csv'}")
    print(f"Wrote {out_dir / 'strong_scaling_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
