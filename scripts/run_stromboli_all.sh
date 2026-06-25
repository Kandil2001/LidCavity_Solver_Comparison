#!/usr/bin/env bash
set -euo pipefail

# Stromboli-friendly runner for the whole project.
# It runs CPU, MPI, Octave, OpenMP, and CUDA parts when the required tools exist.
# Missing optional tools are reported and skipped so one unavailable component
# does not kill the full check.
#
# Examples:
#   bash scripts/run_stromboli_all.sh smoke
#   bash scripts/run_stromboli_all.sh quick
#   RUN_CUDA=1 bash scripts/run_stromboli_all.sh smoke
#   nohup RUN_CUDA=1 bash scripts/run_stromboli_all.sh quick > stromboli_quick.log 2>&1 &

MODE="${1:-smoke}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Make environment modules available in non-interactive shells when possible.
if [ -f /etc/profile.d/modules.sh ]; then
    # shellcheck source=/dev/null
    source /etc/profile.d/modules.sh || true
fi

# Best-effort module/path setup. Unknown module names are harmless.
if type module >/dev/null 2>&1; then
    module load octave >/dev/null 2>&1 || true
    module load openmpi >/dev/null 2>&1 || true
    module load mpi >/dev/null 2>&1 || true
    module load cuda >/dev/null 2>&1 || true
fi

# Stromboli/OpenMPI fallback observed on some university machines.
if [ -d /cluster/mpi/openmpi/4.1.8/bin ]; then
    export PATH="/cluster/mpi/openmpi/4.1.8/bin:$PATH"
    export LD_LIBRARY_PATH="/cluster/mpi/openmpi/4.1.8/lib:${LD_LIBRARY_PATH:-}"
fi

if [ -d /usr/local/cuda/bin ]; then
    export PATH="/usr/local/cuda/bin:$PATH"
fi

print_tool_status() {
    echo "===== Tool status on $(hostname) ====="
    for tool in gcc g++ python3 octave mpirun mpicc nvcc nvidia-smi; do
        if command -v "$tool" >/dev/null 2>&1; then
            printf '%-12s %s\n' "$tool" "$(command -v "$tool")"
        else
            printf '%-12s %s\n' "$tool" "not found"
        fi
    done
    echo
}

run_make_if_folder() {
    local folder="$1"
    shift
    if [ -d "$folder" ]; then
        echo
        echo "==> $folder: make $*"
        make -C "$folder" "$@"
    else
        echo "Skipping $folder: folder not found."
    fi
}

run_octave_if_available() {
    if command -v octave >/dev/null 2>&1; then
        echo
        echo "==> matlab with GNU Octave: $MODE"
        make -C matlab "$MODE" ENGINE=octave
    else
        echo "Skipping MATLAB/Octave: octave not found."
    fi
}

run_mpi_if_available() {
    if command -v mpirun >/dev/null 2>&1; then
        run_make_if_folder python/mpi "$MODE" NP="${NP:-4}"
    else
        echo "Skipping Python MPI: mpirun not found."
    fi

    if command -v mpirun >/dev/null 2>&1 && command -v mpicc >/dev/null 2>&1; then
        run_make_if_folder c/mpi "$MODE" NP="${NP:-4}"
        run_make_if_folder cpp/mpi "$MODE" NP="${NP:-4}"
    else
        echo "Skipping C/C++ MPI: mpirun or mpicc not found."
    fi
}

run_cuda_if_available() {
    if [ "${RUN_CUDA:-1}" = "0" ]; then
        echo "Skipping CUDA because RUN_CUDA=0."
        return 0
    fi
    if ! command -v nvcc >/dev/null 2>&1; then
        echo "Skipping CUDA: nvcc not found."
        return 0
    fi
    if ! command -v nvidia-smi >/dev/null 2>&1; then
        echo "Skipping CUDA: nvidia-smi not found, so no accessible NVIDIA GPU was detected."
        return 0
    fi
    if ! nvidia-smi >/dev/null 2>&1; then
        echo "Skipping CUDA: nvidia-smi could not access a GPU on this node."
        return 0
    fi

    echo
    echo "==> cuda: make $MODE"
    make -C cuda "$MODE"
}

print_tool_status

case "$MODE" in
    smoke|quick|medium|full)
        run_octave_if_available
        run_make_if_folder python/serial "$MODE"
        run_make_if_folder c/serial "$MODE"
        run_make_if_folder cpp/serial "$MODE"
        run_make_if_folder c/openmp "$MODE" OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
        run_make_if_folder cpp/openmp "$MODE" OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
        run_mpi_if_available
        run_cuda_if_available
        ;;
    scaling)
        make scaling-openmp
        make scaling-mpi MODE=smoke || true
        make scaling-cuda || true
        ;;
    *)
        echo "Unknown mode '$MODE'. Use smoke, quick, medium, full, or scaling." >&2
        exit 2
        ;;
esac

echo
echo "Stromboli run finished. Check each results/ folder for generated CSV files."
