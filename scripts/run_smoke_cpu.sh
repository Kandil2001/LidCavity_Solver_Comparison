#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

run_make() {
    local folder="$1"
    shift
    if [[ ! -f "$folder/Makefile" ]]; then
        echo "Missing required Makefile: $folder/Makefile" >&2
        return 1
    fi
    echo
    echo "==> $folder: make $*"
    make -C "$folder" "$@"
}

echo "Running pressure-correction cross-language CPU smoke checks."

if command -v matlab >/dev/null 2>&1 || command -v octave >/dev/null 2>&1; then
    run_make matlab smoke ENGINE="${ENGINE:-auto}"
else
    echo "Skipping MATLAB/Octave smoke check because neither matlab nor octave was found."
fi

run_make python/serial smoke
run_make c/serial smoke
run_make cpp/serial smoke
run_make c/openmp smoke OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
run_make cpp/openmp smoke OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"

if command -v mpirun >/dev/null 2>&1 && command -v mpicc >/dev/null 2>&1; then
    run_make c/mpi smoke NP="${NP:-2}"
else
    echo "Skipping C case-level MPI smoke check because mpicc or mpirun was not found."
fi

if command -v mpirun >/dev/null 2>&1 && command -v mpicxx >/dev/null 2>&1; then
    run_make cpp/mpi smoke NP="${NP:-2}"
else
    echo "Skipping C++ case-level MPI smoke check because mpicxx or mpirun was not found."
fi

if command -v mpirun >/dev/null 2>&1 && python3 -c "import mpi4py" >/dev/null 2>&1; then
    run_make python/mpi smoke NP="${NP:-2}"
else
    echo "Skipping Python case-level MPI smoke check because mpirun or mpi4py was not found."
fi

echo
echo "Pressure-correction CPU smoke checks finished."
echo "The organized streamfunction-vorticity domain track has separate runners under scripts/ and src/."
