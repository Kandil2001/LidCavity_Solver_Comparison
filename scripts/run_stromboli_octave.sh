#!/usr/bin/env bash
set -euo pipefail

# Small helper for Stromboli/cluster runs where MATLAB is unavailable but GNU
# Octave is available.  Usage:
#   bash scripts/run_stromboli_octave.sh smoke
#   bash scripts/run_stromboli_octave.sh quick
#   nohup bash scripts/run_stromboli_octave.sh quick > octave_quick.log 2>&1 &

MODE="${1:-smoke}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Try the module system when it exists.  It is okay if this does nothing.
if type module >/dev/null 2>&1; then
    module load octave >/dev/null 2>&1 || true
fi

if ! command -v octave >/dev/null 2>&1; then
    echo "GNU Octave was not found on PATH." >&2
    echo "Try these on Stromboli:" >&2
    echo "  module avail octave" >&2
    echo "  module load octave" >&2
    echo "Then rerun this script." >&2
    exit 127
fi

echo "Running MATLAB-compatible solver with GNU Octave on $(hostname)."
octave --version | head -n 1

export ENGINE=octave
export OCTAVE_MAKE_FIGURES="${OCTAVE_MAKE_FIGURES:-0}"

case "$MODE" in
    smoke|quick|medium|full|single|plots)
        make -C matlab "$MODE" ENGINE=octave
        ;;
    smoke-cpu)
        make smoke-cpu ENGINE=octave
        ;;
    quick-cpu)
        make quick-cpu ENGINE=octave
        ;;
    *)
        echo "Unknown mode '$MODE'. Use smoke, quick, medium, full, single, plots, smoke-cpu, or quick-cpu." >&2
        exit 2
        ;;
esac
