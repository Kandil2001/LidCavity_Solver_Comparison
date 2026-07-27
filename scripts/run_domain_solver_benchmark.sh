#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

NP=${NP:-4}
OMP_NUM_THREADS=${OMP_NUM_THREADS:-2}
NUMBA_NUM_THREADS=${NUMBA_NUM_THREADS:-2}
N=${N:-64}
RE=${RE:-100}
STEPS=${STEPS:-1000}
POISSON_ITERS=${POISSON_ITERS:-200}
SCHEME=${SCHEME:-upwind}
PYTHON=${PYTHON:-python3}

export OMP_NUM_THREADS
export NUMBA_NUM_THREADS
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

mkdir -p comparison/results/domain_clean logs

RUN_LOG="comparison/results/domain_clean/domain_run_N${N}_Re${RE}_np${NP}_omp${OMP_NUM_THREADS}.log"
: > "$RUN_LOG"

log() {
  echo "$@" | tee -a "$RUN_LOG"
}

run_cmd() {
  local name="$1"
  shift
  log ""
  log "===== $name ====="
  log "Command: $*"
  "$@" 2>&1 | tee -a "$RUN_LOG"
}

log "Domain-decomposition benchmark"
log "NP=$NP OMP_NUM_THREADS=$OMP_NUM_THREADS NUMBA_NUM_THREADS=$NUMBA_NUM_THREADS N=$N RE=$RE STEPS=$STEPS POISSON_ITERS=$POISSON_ITERS SCHEME=$SCHEME"
log "Host: $(hostname)"
log "Start: $(date)"

# Remove previous domain summary files for this clean run.
rm -f c/mpi_domain/results/data/*.csv c/hybrid_mpi_openmp/results/data/*.csv       cpp/mpi_domain/results/data/*.csv cpp/hybrid_mpi_openmp/results/data/*.csv       python/mpi_domain/results/data/*.csv python/hybrid_mpi_openmp/results/data/*.csv

run_cmd "C pure MPI domain" make -C c/mpi_domain run NP="$NP" N="$N" RE="$RE" STEPS="$STEPS" POISSON_ITERS="$POISSON_ITERS" SCHEME="$SCHEME"
run_cmd "C hybrid MPI+OpenMP domain" make -C c/hybrid_mpi_openmp run NP="$NP" OMP_NUM_THREADS="$OMP_NUM_THREADS" N="$N" RE="$RE" STEPS="$STEPS" POISSON_ITERS="$POISSON_ITERS" SCHEME="$SCHEME"
run_cmd "C++ pure MPI domain" make -C cpp/mpi_domain run NP="$NP" N="$N" RE="$RE" STEPS="$STEPS" POISSON_ITERS="$POISSON_ITERS" SCHEME="$SCHEME"
run_cmd "C++ hybrid MPI+OpenMP domain" make -C cpp/hybrid_mpi_openmp run NP="$NP" OMP_NUM_THREADS="$OMP_NUM_THREADS" N="$N" RE="$RE" STEPS="$STEPS" POISSON_ITERS="$POISSON_ITERS" SCHEME="$SCHEME"
run_cmd "Python pure MPI domain" make -C python/mpi_domain run PYTHON="$PYTHON" NP="$NP" N="$N" RE="$RE" STEPS="$STEPS" POISSON_ITERS="$POISSON_ITERS" SCHEME="$SCHEME"
run_cmd "Python hybrid MPI+threaded domain" make -C python/hybrid_mpi_openmp run PYTHON="$PYTHON" NP="$NP" NUMBA_NUM_THREADS="$NUMBA_NUM_THREADS" N="$N" RE="$RE" STEPS="$STEPS" POISSON_ITERS="$POISSON_ITERS" SCHEME="$SCHEME"

log ""
log "===== Compare domain solver times ====="
$PYTHON scripts/compare_domain_solver_times.py 2>&1 | tee -a "$RUN_LOG"

log ""
log "Finished: $(date)"
log "Report: comparison/results/domain_clean/domain_runtime_report.md"
