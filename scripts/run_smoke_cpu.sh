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

if command -v matlab >/dev/null 2>&1; then
    try_make matlab smoke
else
    echo "Skipping MATLAB smoke check because matlab was not found."
fi

try_make python/serial smoke
try_make c/serial smoke
try_make cpp/serial smoke
try_make c/openmp smoke OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
try_make cpp/openmp smoke OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"

if command -v mpirun >/dev/null 2>&1; then
    try_make python/mpi smoke NP="${NP:-2}"
else
    echo "Skipping Python MPI smoke check because mpirun was not found."
fi

if command -v mpicc >/dev/null 2>&1 && command -v mpirun >/dev/null 2>&1; then
    try_make c/mpi smoke NP="${NP:-2}"
    try_make cpp/mpi smoke NP="${NP:-2}"
else
    echo "Skipping C/C++ MPI smoke checks because mpicc or mpirun was not found."
fi

echo
echo "CPU smoke checks finished."
