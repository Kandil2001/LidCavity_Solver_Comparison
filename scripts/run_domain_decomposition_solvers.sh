#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
NP=${NP:-4}
OMP_NUM_THREADS=${OMP_NUM_THREADS:-2}
N=${N:-64}
RE=${RE:-100}
STEPS=${STEPS:-1000}
POISSON_ITERS=${POISSON_ITERS:-200}
SCHEME=${SCHEME:-upwind}

echo "===== Pure MPI domain decomposition ====="
cd "$ROOT_DIR/cpp/mpi_domain"
make build
mpirun -np "$NP" ./bin/mpi_domain_lid_cavity \
    --N "$N" \
    --Re "$RE" \
    --steps "$STEPS" \
    --poisson-iters "$POISSON_ITERS" \
    --output-every 100 \
    --scheme "$SCHEME"

echo "===== Hybrid MPI+OpenMP domain decomposition ====="
cd "$ROOT_DIR/cpp/hybrid_mpi_openmp"
make build
OMP_NUM_THREADS="$OMP_NUM_THREADS" mpirun -np "$NP" ./bin/hybrid_lid_cavity \
    --N "$N" \
    --Re "$RE" \
    --steps "$STEPS" \
    --poisson-iters "$POISSON_ITERS" \
    --output-every 100 \
    --scheme "$SCHEME"
