#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-smoke}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f /etc/profile.d/modules.sh ]]; then
    source /etc/profile.d/modules.sh || true
fi
if type module >/dev/null 2>&1; then
    module load openmpi >/dev/null 2>&1 || true
    module load mpi >/dev/null 2>&1 || true
fi
if [[ -d /cluster/mpi/openmpi/4.1.8/bin ]]; then
    export PATH="/cluster/mpi/openmpi/4.1.8/bin:$PATH"
    export LD_LIBRARY_PATH="/cluster/mpi/openmpi/4.1.8/lib:${LD_LIBRARY_PATH:-}"
fi

for tool in gcc g++ mpicc mpicxx mpirun python3; do
    command -v "$tool" >/dev/null || { echo "Missing required tool: $tool" >&2; exit 1; }
done

case "$MODE" in
    smoke)
        make rebuild-domain
        make smoke-domain \
            NP="${NP:-2}" \
            OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}" \
            NUMBA_NUM_THREADS="${NUMBA_NUM_THREADS:-2}"
        ;;
    one)
        bash scripts/run_domain_solver_benchmark.sh
        ;;
    scaling)
        bash scripts/run_strong_scaling_all.sh
        ;;
    *)
        echo "Usage: $0 [smoke|one|scaling]" >&2
        exit 2
        ;;
esac
