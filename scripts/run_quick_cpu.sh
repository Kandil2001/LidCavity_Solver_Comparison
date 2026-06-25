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

echo "Running quick CPU benchmarks. This can take longer than the smoke check."

if command -v matlab >/dev/null 2>&1 || command -v octave >/dev/null 2>&1; then
    try_make matlab quick ENGINE="${ENGINE:-auto}"
else
    echo "Skipping MATLAB/Octave quick run because neither matlab nor octave was found."
fi

try_make python/serial quick
try_make c/serial quick
try_make cpp/serial quick
try_make c/openmp quick OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
try_make cpp/openmp quick OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"

if command -v mpirun >/dev/null 2>&1; then
    try_make python/mpi quick NP="${NP:-4}"
else
    echo "Skipping Python MPI quick run because mpirun was not found."
fi

if command -v mpicc >/dev/null 2>&1 && command -v mpirun >/dev/null 2>&1; then
    try_make c/mpi quick NP="${NP:-4}"
    try_make cpp/mpi quick NP="${NP:-4}"
else
    echo "Skipping C/C++ MPI quick runs because mpicc or mpirun was not found."
fi

echo
echo "Quick CPU benchmark run finished."
