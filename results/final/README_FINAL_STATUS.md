# Archived CPU and CUDA result status

> **Track:** These CPU results belong to the streamfunction–vorticity domain-scaling study. They are fixed-step execution measurements and are not the same numerical benchmark as the original pressure-correction solvers under the repository root.

See [`../../docs/BENCHMARK_TRACKS.md`](../../docs/BENCHMARK_TRACKS.md) before comparing these files with `comparison/results/`.

## CPU execution completeness

| Family | Cases found | Successful rows | Failed or time-limited rows | Notes |
|---|---:|---:|---:|---|
| OpenMP | 18 | 2,160 | 0 | Complete execution archive for the configured C/C++ domain solvers |
| MPI domain | 18 | 1,061 | 2,140 | Case 13 contains salvaged successful rows |
| Hybrid MPI + threading | 18 | 1,044 | 2,100 | Case 13 contains salvaged successful rows |

A successful row means the command completed and produced a readable summary. The domain solvers use configured step counts, so process success does not automatically establish numerical convergence or external validation.

## CUDA archive

### Exact CUDA RBGS/RBSOR run

- 108 data rows: 54 RBGS and 54 RBSOR.
- All 108 rows currently have `ValidationPass = 0` under the configured Ghia thresholds.

### Older Jacobi CUDA run

- 22 retained data rows.
- Kept as historical prototype evidence.

The CUDA implementation is projection-based and is not numerically identical to the streamfunction–vorticity CPU domain archive. CPU/CUDA runtime plots are therefore exploratory engineering measurements, not a validated same-algorithm speedup study.

## Safe usage of this archive

Use these files for:

- execution completeness and failure-rate analysis;
- fixed-step runtime distributions;
- OpenMP, MPI, and hybrid scaling diagnostics;
- RBGS versus RBSOR execution comparisons when the full configuration matches;
- identifying cases that need rerunning.

Do not use them alone for:

- a final time-to-convergence ranking;
- a final fastest-language claim;
- a validated CPU-versus-GPU speedup;
- a claim that `status=success` means the CFD solution converged;
- a broad ranking based only on the minimum observed runtime.

## Special cases

- MPI and hybrid case 13 were partially salvaged from successful rows. Failed and time-limited rows remain part of the completeness record.
- Current scaling reports should keep pressure solver, kernel style, language, core count, rank count, thread count, and repetition explicit.
- Numerical convergence and validation fields should be added before any future final rerun matrix is interpreted scientifically.
