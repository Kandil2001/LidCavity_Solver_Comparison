#!/bin/bash
set -euo pipefail

NP=${NP:-2}
OMP_NUM_THREADS=${OMP_NUM_THREADS:-2}
NUMBA_NUM_THREADS=${NUMBA_NUM_THREADS:-2}
N=${N:-64}
RE=${RE:-100}
STEPS=${STEPS:-500}
POISSON_ITERS=${POISSON_ITERS:-100}
SCHEME=${SCHEME:-upwind}

run_make() {
  local dir="$1"
  shift
  echo
  echo "===== $dir ====="
  (cd "$dir" && "$@")
}

run_make c/mpi_domain make quick NP="$NP" N="$N" RE="$RE" STEPS="$STEPS" POISSON_ITERS="$POISSON_ITERS" SCHEME="$SCHEME"
run_make c/hybrid_mpi_openmp make quick NP="$NP" OMP_NUM_THREADS="$OMP_NUM_THREADS" N="$N" RE="$RE" STEPS="$STEPS" POISSON_ITERS="$POISSON_ITERS" SCHEME="$SCHEME"
run_make cpp/mpi_domain make quick NP="$NP" N="$N" RE="$RE" STEPS="$STEPS" POISSON_ITERS="$POISSON_ITERS" SCHEME="$SCHEME"
run_make cpp/hybrid_mpi_openmp make quick NP="$NP" OMP_NUM_THREADS="$OMP_NUM_THREADS" N="$N" RE="$RE" STEPS="$STEPS" POISSON_ITERS="$POISSON_ITERS" SCHEME="$SCHEME"
run_make python/mpi_domain make quick NP="$NP" N="$N" RE="$RE" STEPS="$STEPS" POISSON_ITERS="$POISSON_ITERS" SCHEME="$SCHEME"
run_make python/hybrid_mpi_openmp make quick NP="$NP" NUMBA_NUM_THREADS="$NUMBA_NUM_THREADS" N="$N" RE="$RE" STEPS="$STEPS" POISSON_ITERS="$POISSON_ITERS" SCHEME="$SCHEME"
