# Current benchmark results

## Reviewed headline case

The root README uses one repeated archived domain case:

```text
N=128, Re=400, central, RBSOR
2500 outer steps, 250 Poisson iterations per step
3 repetitions per resource configuration
```

Best retained vectorized points:

| Implementation | Resources | Median runtime | Speedup | Efficiency |
|---|---:|---:|---:|---:|
| C OpenMP | 4 threads | 6.688 s | 2.346× | 58.6% |
| C++ OpenMP | 4 threads | 6.627 s | 2.348× | 58.7% |
| Python spatial MPI | 16 ranks | 53.748 s | 6.202× | 38.8% |
| Python hybrid | 4 ranks × 2 threads | 109.364 s | 3.003× | 37.5% |

The source rows are generated in `results/selected/` from the complete archive.

## Archive completeness

| Family | Successful rows | Failed/time-limited rows |
|---|---:|---:|
| OpenMP | 2,160 | 0 |
| Spatial MPI | 1,061 | 2,140 |
| Hybrid | 1,044 | 2,100 |

The retained successful MPI and hybrid rows are Python. Historical C/C++ distributed runs failed to rebuild; their Makefiles are fixed, but their performance cases require rerunning.

## Valid interpretation

- The C and C++ OpenMP implementations have nearly identical runtime in the selected case.
- Four threads are the useful archived OpenMP point for this workload.
- Python pure MPI is faster than the archived Python hybrid layout.
- Results are repeated fixed-step timings.

## Not yet supported

- convergence-controlled time-to-solution;
- a C/C++/Python distributed-memory ranking;
- validated CPU/GPU speedup;
- one ranking that combines the pressure-correction and streamfunction–vorticity methods.
