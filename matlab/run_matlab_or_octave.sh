#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-smoke}"
ENGINE="${ENGINE:-auto}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

case "$MODE" in
    smoke|quick|medium|full)
        OCTAVE_CMD="addpath('src/app'); run_${MODE}"
        MATLAB_CMD="addpath('src/app'); run_${MODE}"
        ;;
    single)
        OCTAVE_CMD="addpath('src/app'); addpath('src/studies'); run_single_case"
        MATLAB_CMD="addpath('src/app'); addpath('src/studies'); run_single_case"
        ;;
    plots)
        OCTAVE_CMD="addpath('src/app'); generate_all_plots_from_results"
        MATLAB_CMD="addpath('src/app'); generate_all_plots_from_results"
        ;;
    *)
        echo "Unknown mode '$MODE'. Use smoke, quick, medium, full, single, or plots." >&2
        exit 2
        ;;
esac

run_matlab() {
    matlab -batch "$MATLAB_CMD"
}

run_octave() {
    octave --quiet --eval "$OCTAVE_CMD"
}

if [ "$ENGINE" = "matlab" ]; then
    command -v matlab >/dev/null 2>&1 || { echo "matlab was not found." >&2; exit 127; }
    echo "Using MATLAB for $MODE."
    run_matlab
elif [ "$ENGINE" = "octave" ]; then
    command -v octave >/dev/null 2>&1 || { echo "octave was not found. Try: module avail octave; module load octave" >&2; exit 127; }
    echo "Using GNU Octave for $MODE."
    run_octave
else
    if command -v matlab >/dev/null 2>&1; then
        echo "Using MATLAB for $MODE. Set ENGINE=octave to force GNU Octave."
        run_matlab
    elif command -v octave >/dev/null 2>&1; then
        echo "Using GNU Octave for $MODE."
        run_octave
    else
        echo "Neither matlab nor octave was found. Try loading Octave on the cluster first:" >&2
        echo "  module avail octave" >&2
        echo "  module load octave" >&2
        exit 127
    fi
fi
