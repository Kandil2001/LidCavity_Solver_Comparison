#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
MODE="${1:-reference}"

run_make() {
    local folder="$1"
    shift
    [[ -f "$folder/Makefile" ]] || { echo "Missing required Makefile: $folder/Makefile" >&2; return 1; }
    echo
    echo "==> $folder: make $*"
    make -C "$folder" "$@"
}

case "$MODE" in
    reference)
        echo "Running the pressure-correction serial/OpenMP reference smoke tests."
        if command -v matlab >/dev/null 2>&1 || command -v octave >/dev/null 2>&1; then
            run_make matlab smoke ENGINE="${ENGINE:-auto}"
        else
            echo "Skipping MATLAB/Octave because neither executable is available."
        fi
        run_make python/serial smoke NO_FIELDS=1
        run_make c/serial smoke NO_FIELDS=1
        run_make cpp/serial smoke NO_FIELDS=1
        run_make c/openmp smoke OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}" NO_FIELDS=1
        run_make cpp/openmp smoke OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}" NO_FIELDS=1
        ;;
    domain)
        make smoke-domain \
            NP="${NP:-2}" \
            OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}" \
            NUMBA_NUM_THREADS="${NUMBA_NUM_THREADS:-2}"
        ;;
    all)
        "$0" reference
        "$0" domain
        ;;
    *)
        echo "Usage: $0 [reference|domain|all]" >&2
        exit 2
        ;;
esac
