# Continuous Integration

The repository includes a CPU-only GitHub Actions workflow at:

```text
.github/workflows/cpu-smoke.yml
```

## What the workflow checks

The workflow installs OpenMPI and a pinned Python environment, then runs:

```bash
make smoke-cpu NP=2 OMP_NUM_THREADS=2
```

On the GitHub-hosted Linux runner, this exercises the available CPU groups:

- Python serial
- C serial
- C++ serial
- C OpenMP
- C++ OpenMP
- Python MPI with two ranks
- C MPI with two ranks
- C++ MPI with two ranks

MATLAB/Octave is skipped when neither executable is available. CUDA is not part of this workflow because GitHub's standard hosted runner does not provide the project GPU environment.

After execution, the workflow checks that each tested solver group produced at least one non-empty study summary containing data rows.

## What a green workflow proves

A green workflow proves that the tested CPU implementations can be built or imported, start their smallest configured case, finish that configured smoke run, and write readable summary output in the pinned CI environment.

It does **not** prove that:

- the full benchmark cases satisfy residual-convergence criteria
- all implementations are numerically equivalent
- current runtime rankings are portable to other hardware
- MATLAB/Octave or CUDA paths are working
- the project is ready for a stable benchmark release

These distinctions match the repository's separation between execution completion, convergence, validation status, and performance measurement.

## CI dependency baseline

The workflow dependency versions are recorded in:

```text
.github/requirements-ci.txt
```

This file is intentionally separate from the general user-facing requirements files. It keeps the automated smoke environment stable without claiming that every scientific production run must use the same plotting-library versions.
