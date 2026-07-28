#!/bin/bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

SRC_ROOT=${SRC_ROOT:-src}
NP=${NP:-4}
OMP_NUM_THREADS=${OMP_NUM_THREADS:-2}
NUMBA_NUM_THREADS=${NUMBA_NUM_THREADS:-2}
N=${N:-64}
RE=${RE:-100}
STEPS=${STEPS:-1000}
POISSON_ITERS=${POISSON_ITERS:-200}
SCHEME=${SCHEME:-upwind}
POISSON_SOLVER=${POISSON_SOLVER:-RBGS}
SOR_OMEGA=${SOR_OMEGA:-1.7}
PYTHON=${PYTHON:-python3}

export OMP_NUM_THREADS
export NUMBA_NUM_THREADS
export OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-1}
export MKL_NUM_THREADS=${MKL_NUM_THREADS:-1}
export NUMEXPR_NUM_THREADS=${NUMEXPR_NUM_THREADS:-1}

mkdir -p comparison/results/domain_kernel_matrix logs
RUN_LOG="comparison/results/domain_kernel_matrix/run_N${N}_Re${RE}_${POISSON_SOLVER}_np${NP}_omp${OMP_NUM_THREADS}_numba${NUMBA_NUM_THREADS}.log"
: > "$RUN_LOG"
log(){ echo "$@" | tee -a "$RUN_LOG"; }
run_cmd(){ local name="$1"; shift; log ""; log "===== $name ====="; log "Command: $*"; "$@" 2>&1 | tee -a "$RUN_LOG"; }

SOLVER_DIRS=(
"$SRC_ROOT/c/mpi_domain_looped"
"$SRC_ROOT/c/mpi_domain_vectorized"
"$SRC_ROOT/c/hybrid_mpi_openmp_looped"
"$SRC_ROOT/c/hybrid_mpi_openmp_vectorized"
"$SRC_ROOT/cpp/mpi_domain_looped"
"$SRC_ROOT/cpp/mpi_domain_vectorized"
"$SRC_ROOT/cpp/hybrid_mpi_openmp_looped"
"$SRC_ROOT/cpp/hybrid_mpi_openmp_vectorized"
"$SRC_ROOT/python/mpi_domain_looped"
"$SRC_ROOT/python/mpi_domain_vectorized"
"$SRC_ROOT/python/hybrid_mpi_openmp_looped"
"$SRC_ROOT/python/hybrid_mpi_openmp_vectorized"
)
for dir in "${SOLVER_DIRS[@]}"; do
    if [[ ! -f "$dir/Makefile" ]]; then
        echo "ERROR: missing solver Makefile: $dir/Makefile" >&2
        echo "Set SRC_ROOT if the organized source tree is stored elsewhere." >&2
        exit 2
    fi
done

log "Domain-decomposition kernel matrix benchmark"
log "SRC_ROOT=$SRC_ROOT"
log "NP=$NP OMP_NUM_THREADS=$OMP_NUM_THREADS NUMBA_NUM_THREADS=$NUMBA_NUM_THREADS N=$N RE=$RE STEPS=$STEPS POISSON_ITERS=$POISSON_ITERS SCHEME=$SCHEME POISSON_SOLVER=$POISSON_SOLVER SOR_OMEGA=$SOR_OMEGA"
log "Host: $(hostname)"
log "Start: $(date)"

# Clean only generated summary/field CSVs for this organized domain-solver matrix.
find "$SRC_ROOT/c" "$SRC_ROOT/cpp" "$SRC_ROOT/python" -maxdepth 4 -path '*/results/data/*.csv' -type f -delete || true

COMMON=(N="$N" RE="$RE" STEPS="$STEPS" POISSON_ITERS="$POISSON_ITERS" SCHEME="$SCHEME" POISSON_SOLVER="$POISSON_SOLVER" SOR_OMEGA="$SOR_OMEGA" NO_FIELDS=1)

run_cmd "C MPI domain looped" make -C "$SRC_ROOT/c/mpi_domain_looped" run NP="$NP" "${COMMON[@]}"
run_cmd "C MPI domain vectorized" make -C "$SRC_ROOT/c/mpi_domain_vectorized" run NP="$NP" "${COMMON[@]}"
run_cmd "C hybrid MPI+OpenMP looped" make -C "$SRC_ROOT/c/hybrid_mpi_openmp_looped" run NP="$NP" OMP_NUM_THREADS="$OMP_NUM_THREADS" "${COMMON[@]}"
run_cmd "C hybrid MPI+OpenMP vectorized" make -C "$SRC_ROOT/c/hybrid_mpi_openmp_vectorized" run NP="$NP" OMP_NUM_THREADS="$OMP_NUM_THREADS" "${COMMON[@]}"

run_cmd "C++ MPI domain looped" make -C "$SRC_ROOT/cpp/mpi_domain_looped" run NP="$NP" "${COMMON[@]}"
run_cmd "C++ MPI domain vectorized" make -C "$SRC_ROOT/cpp/mpi_domain_vectorized" run NP="$NP" "${COMMON[@]}"
run_cmd "C++ hybrid MPI+OpenMP looped" make -C "$SRC_ROOT/cpp/hybrid_mpi_openmp_looped" run NP="$NP" OMP_NUM_THREADS="$OMP_NUM_THREADS" "${COMMON[@]}"
run_cmd "C++ hybrid MPI+OpenMP vectorized" make -C "$SRC_ROOT/cpp/hybrid_mpi_openmp_vectorized" run NP="$NP" OMP_NUM_THREADS="$OMP_NUM_THREADS" "${COMMON[@]}"

run_cmd "Python MPI domain looped" make -C "$SRC_ROOT/python/mpi_domain_looped" run PYTHON="$PYTHON" NP="$NP" "${COMMON[@]}"
run_cmd "Python MPI domain vectorized" make -C "$SRC_ROOT/python/mpi_domain_vectorized" run PYTHON="$PYTHON" NP="$NP" "${COMMON[@]}"
run_cmd "Python hybrid MPI+threaded looped" make -C "$SRC_ROOT/python/hybrid_mpi_openmp_looped" run PYTHON="$PYTHON" NP="$NP" NUMBA_NUM_THREADS="$NUMBA_NUM_THREADS" "${COMMON[@]}"
run_cmd "Python hybrid MPI+threaded vectorized" make -C "$SRC_ROOT/python/hybrid_mpi_openmp_vectorized" run PYTHON="$PYTHON" NP="$NP" NUMBA_NUM_THREADS="$NUMBA_NUM_THREADS" "${COMMON[@]}"

log ""
log "===== Compare 12-solver matrix ====="
SRC_ROOT="$SRC_ROOT" "$PYTHON" scripts/compare_domain_kernel_matrix.py 2>&1 | tee -a "$RUN_LOG"
log "Finished: $(date)"
log "Report: comparison/results/domain_kernel_matrix/domain_kernel_matrix_report.md"
