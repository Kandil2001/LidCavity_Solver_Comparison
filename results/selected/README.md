# Selected archived results

This directory contains the small result set used by the root README.
It is generated from the existing repeated **grid/domain-decomposition** archive by:

```bash
python3 scripts/generate_selected_results.py
```

No CFD case is executed by that command.

## Representative fixed workload

- Grid: `N = 128`
- Reynolds number: `Re = 400`
- Convection scheme: `central`
- Poisson method: `RBSOR`
- Outer steps: `2500`
- Poisson iterations per step: `250`
- Repetitions per configuration: `3`

| Implementation | Best archived configuration | Median runtime [s] | Speedup | Efficiency |
|---|---:|---:|---:|---:|
| C OpenMP vectorized | 4 threads | 6.688 | 2.346× | 58.6% |
| C++ OpenMP vectorized | 4 threads | 6.627 | 2.348× | 58.7% |
| Python pure-MPI vectorized | 16 ranks | 53.748 | 6.202× | 38.8% |
| Python hybrid vectorized | 4 ranks × 2 threads | 109.364 | 3.003× | 37.5% |

The C and C++ MPI/hybrid archive rows are not included because those historical jobs did not rebuild successfully. The Makefiles are repaired in the repository, but those configurations require rerunning before a cross-language distributed-memory comparison can be made.

## Interpretation

- C and C++ OpenMP performance is nearly identical for the selected vectorized workload.
- Four OpenMP threads are the useful point in this archived case; runtime increases beyond that.
- Python pure MPI scales better than the Python hybrid layout for this workload.
- These are fixed-step performance measurements, not convergence-controlled time-to-solution results.

## Files

- `scaling_case_n128_re400_central_rbsor.csv`: every retained scaling point for the selected case.
- `highlights.csv`: best vectorized point per solver.
- `execution_completeness.csv`: execution success/failure totals for the archived grid-decomposition study.
