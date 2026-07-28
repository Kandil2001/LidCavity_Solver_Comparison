# Contributing

Contributions should improve clarity, reproducibility, numerical verification, or benchmark quality without mixing incompatible methods.

## Before changing solver behavior

Document:

- the affected implementation and numerical track;
- the mathematical or algorithmic change;
- expected effects on fields, convergence, and runtime;
- which archived tables must be regenerated;
- the verification used to establish correctness.

## Required checks

```bash
make check
make rebuild-domain
make smoke-cpu NP=2 OMP_NUM_THREADS=2 NUMBA_NUM_THREADS=2
make selected-results
git diff --exit-code -- results/selected
```

A focused implementation can also be checked directly, for example:

```bash
make -C src/cpp/mpi_domain_vectorized smoke NP=2
```

## Repository rules

- MPI implementations must spatially decompose one grid.
- Do not add parameter-sweep scheduling as an MPI solver comparison.
- Keep the pressure-correction and streamfunction–vorticity tracks separate.
- Do not commit binaries, caches, backup files, temporary logs, or ad-hoc packaged archives.
- Raw result archives must retain configuration and repetition metadata.
- Headline results must use matched configurations and repeated statistics.
- Do not present execution completion as numerical convergence or validation.

## Pull requests

Use a focused branch and explain what changed, why it changed, how it was tested, whether results changed, and what still requires HPC rerunning.
