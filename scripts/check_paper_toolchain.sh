#!/usr/bin/env bash

# Check which paper-benchmark tools are available without requiring sudo.
# Run with:
#   bash scripts/check_paper_toolchain.sh
# or save the report with:
#   bash scripts/check_paper_toolchain.sh --output comparison/results/toolchain/stromboli.txt

set -uo pipefail

OUTPUT=""
if [[ ${1:-} == "--output" ]]; then
    OUTPUT=${2:-}
    if [[ -z "$OUTPUT" ]]; then
        echo "error: --output requires a path" >&2
        exit 2
    fi
    mkdir -p "$(dirname "$OUTPUT")"
fi

emit() {
    printf '%s\n' "$*"
}

command_version() {
    local label=$1
    local command_name=$2
    shift 2

    if command -v "$command_name" >/dev/null 2>&1; then
        emit "[available] $label"
        emit "  path: $(command -v "$command_name")"
        local version_output
        version_output=$("$command_name" "$@" 2>&1 | head -n 3 || true)
        if [[ -n "$version_output" ]]; then
            while IFS= read -r line; do
                emit "  $line"
            done <<< "$version_output"
        fi
    else
        emit "[missing]   $label ($command_name)"
    fi
}

run_report() {
    emit "LidCavity paper toolchain report"
    emit "generated_utc: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    emit "hostname: $(hostname 2>/dev/null || echo unknown)"
    emit "kernel: $(uname -srmo 2>/dev/null || echo unknown)"
    emit "working_directory: $(pwd)"
    emit ""

    emit "== Core serial toolchains =="
    command_version "Python" python3 --version
    command_version "GCC" gcc --version
    command_version "G++" g++ --version
    command_version "Make" make --version
    emit ""

    emit "== Rust check =="
    command_version "Rust compiler" rustc --version
    command_version "Cargo" cargo --version
    emit ""

    emit "== Parallel tooling =="
    command_version "MPI compiler (C)" mpicc --version
    command_version "MPI compiler (C++)" mpicxx --version
    command_version "MPI launcher" mpirun --version
    command_version "Slurm submit" sbatch --version
    command_version "Slurm run" srun --version
    emit ""

    emit "== OpenFOAM check =="
    command_version "OpenFOAM version helper" foamVersion
    command_version "OpenFOAM generic runner" foamRun -help
    command_version "OpenFOAM icoFoam" icoFoam -help
    command_version "OpenFOAM simpleFoam" simpleFoam -help
    command_version "OpenFOAM pimpleFoam" pimpleFoam -help
    emit ""

    emit "== Optional GPU tooling =="
    command_version "CUDA compiler" nvcc --version
    command_version "NVIDIA status" nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
    emit ""

    emit "== Hardware summary =="
    if command -v lscpu >/dev/null 2>&1; then
        lscpu | grep -E '^(Architecture|CPU\(s\)|Model name|Thread\(s\) per core|Core\(s\) per socket|Socket\(s\)|NUMA node\(s\)):' || true
    else
        emit "lscpu unavailable"
    fi
    emit ""

    emit "== Interpretation =="
    if command -v rustc >/dev/null 2>&1 && command -v cargo >/dev/null 2>&1; then
        emit "rust_status: available"
    else
        emit "rust_status: unavailable_on_current_path"
    fi

    if command -v foamVersion >/dev/null 2>&1 || command -v foamRun >/dev/null 2>&1 || command -v icoFoam >/dev/null 2>&1; then
        emit "openfoam_status: available"
    else
        emit "openfoam_status: unavailable_or_environment_not_loaded"
    fi
}

if [[ -n "$OUTPUT" ]]; then
    run_report | tee "$OUTPUT"
else
    run_report
fi
