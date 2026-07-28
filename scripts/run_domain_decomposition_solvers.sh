#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC_ROOT=${SRC_ROOT:-src}
KERNEL_STYLE=${KERNEL_STYLE:-vectorized}

case "$KERNEL_STYLE" in
    looped|vectorized) ;;
    *) echo "KERNEL_STYLE must be looped or vectorized" >&2; exit 2 ;;
esac

MPI_DIR="$ROOT_DIR/$SRC_ROOT/cpp/mpi_domain_${KERNEL_STYLE}"
HYBRID_DIR="$ROOT_DIR/$SRC_ROOT/cpp/hybrid_mpi_openmp_${KERNEL_STYLE}"
for dir in "$MPI_DIR" "$HYBRID_DIR"; do
    if [[ ! -f "$dir/Makefile" ]]; then
        echo "Missing solver Makefile: $dir/Makefile" >&2
        exit 2
    fi
done

NP=${NP:-4}
OMP_NUM_THREADS=${OMP_NUM_THREADS:-2}
N=${N:-64}
RE=${RE:-100}
STEPS=${STEPS:-1000}
POISSON_ITERS=${POISSON_ITERS:-200}
SCHEME=${SCHEME:-upwind}
POISSON_SOLVER=${POISSON_SOLVER:-RBGS}
SOR_OMEGA=${SOR_OMEGA:-1.7}
NO_FIELDS=${NO_FIELDS:-1}

COMMON=(N="$N" RE="$RE" STEPS="$STEPS" POISSON_ITERS="$POISSON_ITERS" SCHEME="$SCHEME" POISSON_SOLVER="$POISSON_SOLVER" SOR_OMEGA="$SOR_OMEGA" NO_FIELDS="$NO_FIELDS")

echo "===== Pure MPI domain decomposition: $KERNEL_STYLE ====="
make -C "$MPI_DIR" run NP="$NP" "${COMMON[@]}"

echo "===== Hybrid MPI+OpenMP domain decomposition: $KERNEL_STYLE ====="
OMP_NUM_THREADS="$OMP_NUM_THREADS" make -C "$HYBRID_DIR" run NP="$NP" OMP_NUM_THREADS="$OMP_NUM_THREADS" "${COMMON[@]}"
