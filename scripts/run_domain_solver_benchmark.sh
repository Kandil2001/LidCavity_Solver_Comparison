#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

NP="${NP:-4}"
OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}"
NUMBA_NUM_THREADS="${NUMBA_NUM_THREADS:-2}"
N="${N:-64}"
RE="${RE:-100}"
STEPS="${STEPS:-1000}"
POISSON_ITERS="${POISSON_ITERS:-200}"
SCHEME="${SCHEME:-central}"
POISSON_SOLVER="${POISSON_SOLVER:-RBSOR}"
KERNEL_STYLE="${KERNEL_STYLE:-vectorized}"
PYTHON="${PYTHON:-python3}"

case "$KERNEL_STYLE" in
    looped|vectorized) ;;
    *) echo "KERNEL_STYLE must be looped or vectorized" >&2; exit 2 ;;
esac

required=(
    "src/c/openmp_domain_${KERNEL_STYLE}"
    "src/cpp/openmp_domain_${KERNEL_STYLE}"
    "src/c/mpi_domain_${KERNEL_STYLE}"
    "src/cpp/mpi_domain_${KERNEL_STYLE}"
    "src/python/mpi_domain_${KERNEL_STYLE}"
    "src/c/hybrid_mpi_openmp_${KERNEL_STYLE}"
    "src/cpp/hybrid_mpi_openmp_${KERNEL_STYLE}"
    "src/python/hybrid_mpi_openmp_${KERNEL_STYLE}"
)

for directory in "${required[@]}"; do
    [[ -f "$directory/Makefile" ]] || { echo "Missing $directory/Makefile" >&2; exit 1; }
done

common=(
    "N=$N" "RE=$RE" "STEPS=$STEPS" "POISSON_ITERS=$POISSON_ITERS"
    "SCHEME=$SCHEME" "POISSON_SOLVER=$POISSON_SOLVER" "NO_FIELDS=1"
)

run() {
    local label="$1"
    local directory="$2"
    shift 2
    echo
    echo "==> $label"
    make -C "$directory" run "${common[@]}" "$@"
}

run "C OpenMP $KERNEL_STYLE" "src/c/openmp_domain_${KERNEL_STYLE}" "OMP_NUM_THREADS=$OMP_NUM_THREADS"
run "C++ OpenMP $KERNEL_STYLE" "src/cpp/openmp_domain_${KERNEL_STYLE}" "OMP_NUM_THREADS=$OMP_NUM_THREADS"
run "C spatial MPI $KERNEL_STYLE" "src/c/mpi_domain_${KERNEL_STYLE}" "NP=$NP"
run "C++ spatial MPI $KERNEL_STYLE" "src/cpp/mpi_domain_${KERNEL_STYLE}" "NP=$NP"
run "Python spatial MPI $KERNEL_STYLE" "src/python/mpi_domain_${KERNEL_STYLE}" "NP=$NP" "PYTHON=$PYTHON"
run "C hybrid $KERNEL_STYLE" "src/c/hybrid_mpi_openmp_${KERNEL_STYLE}" "NP=$NP" "OMP_NUM_THREADS=$OMP_NUM_THREADS"
run "C++ hybrid $KERNEL_STYLE" "src/cpp/hybrid_mpi_openmp_${KERNEL_STYLE}" "NP=$NP" "OMP_NUM_THREADS=$OMP_NUM_THREADS"
run "Python hybrid $KERNEL_STYLE" "src/python/hybrid_mpi_openmp_${KERNEL_STYLE}" "NP=$NP" "NUMBA_NUM_THREADS=$NUMBA_NUM_THREADS" "PYTHON=$PYTHON"
