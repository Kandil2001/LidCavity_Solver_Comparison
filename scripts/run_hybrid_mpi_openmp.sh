#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
cd cpp/hybrid_mpi_openmp

NP=${NP:-4}
OMP_NUM_THREADS=${OMP_NUM_THREADS:-2}
N=${N:-64}
RE=${RE:-100}
STEPS=${STEPS:-1000}
POISSON_ITERS=${POISSON_ITERS:-200}
SCHEME=${SCHEME:-upwind}

export OMP_NUM_THREADS
make build
mpirun -np "$NP" ./bin/hybrid_lid_cavity \
    --N "$N" \
    --Re "$RE" \
    --steps "$STEPS" \
    --poisson-iters "$POISSON_ITERS" \
    --scheme "$SCHEME" \
    --output-every 100
