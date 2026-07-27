#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

run_make() {
    local folder="$1"
    shift
    echo
    echo "==> $folder: make $*"
    make -C "$folder" "$@"
}

try_make() {
    local folder="$1"
    shift
    if [ ! -d "$folder" ]; then
        echo "Skipping $folder because the folder is missing."
        return 0
    fi
    run_make "$folder" "$@"
}

echo "Running CPU smoke checks. Missing optional tools are skipped."

if command -v matlab >/dev/null 2>&1 || command -v octave >/dev/null 2>&1; then
    try_make matlab smoke ENGINE="${ENGINE:-auto}"
else
    echo "Skipping MATLAB/Octave smoke check because neither matlab nor octave was found."
fi

try_make python/serial smoke
try_make c/serial smoke
try_make cpp/serial smoke
try_make c/openmp smoke OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
try_make cpp/openmp smoke OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"

if command -v mpirun >/dev/null 2>&1 && command -v mpicc >/dev/null 2>&1; then
    try_make c/mpi_domain smoke NP="${NP:-2}"
    try_make c/hybrid_mpi_openmp smoke NP="${NP:-2}" OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}"
else
    echo "Skipping C domain MPI smoke checks because mpicc or mpirun was not found."
fi

if command -v mpirun >/dev/null 2>&1 && command -v mpicxx >/dev/null 2>&1; then
    try_make cpp/mpi_domain smoke NP="${NP:-2}"
    try_make cpp/hybrid_mpi_openmp smoke NP="${NP:-2}" OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}"
else
    echo "Skipping C++ domain MPI smoke checks because mpicxx or mpirun was not found."
fi

if command -v mpirun >/dev/null 2>&1 && python3 -c "import mpi4py" >/dev/null 2>&1; then
    try_make python/mpi_domain smoke NP="${NP:-2}"
    try_make python/hybrid_mpi_openmp smoke NP="${NP:-2}" NUMBA_NUM_THREADS="${NUMBA_NUM_THREADS:-2}"
else
    echo "Skipping Python domain MPI smoke checks because mpirun or mpi4py was not found."
fi

echo
echo "CPU smoke checks finished."
