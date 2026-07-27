#!/bin/bash
#SBATCH --job-name=lid-strong-scaling
#SBATCH --output=logs/strong_scaling_%j.out
#SBATCH --error=logs/strong_scaling_%j.err
#SBATCH --ntasks=16
#SBATCH --cpus-per-task=1
#SBATCH --time=12:00:00
#SBATCH --mem=8G

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$PWD}"
mkdir -p logs comparison/results/strong_scaling

module load openmpi 2>/dev/null || module load mpi 2>/dev/null || true

# Defaults can be overridden at submission time, for example:
# sbatch --ntasks=16 jobs/run_strong_scaling_all.sbatch
export PYTHON=${PYTHON:-python3}
export RANKS=${RANKS:-"1 2 4 8 16"}
export THREADS_LIST=${THREADS_LIST:-"1 2 4 8 16"}
export HYBRID_PAIRS=${HYBRID_PAIRS:-"1x1 1x2 2x2 4x2 4x4"}
export CASES=${CASES:-"64:100:upwind:1000:200 128:1000:upwind:2000:250"}
export REPEATS=${REPEATS:-1}
export RESET_RESULTS=${RESET_RESULTS:-1}
export CONTINUE_ON_ERROR=${CONTINUE_ON_ERROR:-1}
export PLOTS=${PLOTS:-1}

bash scripts/run_strong_scaling_all.sh
