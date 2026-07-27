#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/../cpp/mpi_domain"

NP=${NP:-4}
N=${N:-64}
RE=${RE:-100}
STEPS=${STEPS:-1000}
POISSON_ITERS=${POISSON_ITERS:-200}
SCHEME=${SCHEME:-upwind}

make build
mpirun -np "$NP" ./bin/mpi_domain_lid_cavity \
    --N "$N" \
    --Re "$RE" \
    --steps "$STEPS" \
    --poisson-iters "$POISSON_ITERS" \
    --output-every 100 \
    --scheme "$SCHEME"
