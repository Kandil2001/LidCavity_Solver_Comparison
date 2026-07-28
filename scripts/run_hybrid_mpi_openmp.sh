#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC_ROOT=${SRC_ROOT:-src}
KERNEL_STYLE=${KERNEL_STYLE:-vectorized}

case "$KERNEL_STYLE" in
    looped|vectorized) ;;
    *) echo "KERNEL_STYLE must be looped or vectorized" >&2; exit 2 ;;
esac

SOLVER_DIR="$ROOT_DIR/$SRC_ROOT/cpp/hybrid_mpi_openmp_${KERNEL_STYLE}"
if [[ ! -f "$SOLVER_DIR/Makefile" ]]; then
    echo "Missing solver Makefile: $SOLVER_DIR/Makefile" >&2
    exit 2
fi

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

export OMP_NUM_THREADS
make -C "$SOLVER_DIR" run \
    NP="$NP" OMP_NUM_THREADS="$OMP_NUM_THREADS" N="$N" RE="$RE" \
    STEPS="$STEPS" POISSON_ITERS="$POISSON_ITERS" SCHEME="$SCHEME" \
    POISSON_SOLVER="$POISSON_SOLVER" SOR_OMEGA="$SOR_OMEGA" NO_FIELDS="$NO_FIELDS"
