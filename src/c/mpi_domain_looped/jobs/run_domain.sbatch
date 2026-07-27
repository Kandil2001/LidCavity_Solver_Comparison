#!/bin/bash
#SBATCH --job-name=c_mpi_domain
#SBATCH --output=results/c_mpi_domain_%j.out
#SBATCH --error=results/c_mpi_domain_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=02:00:00

set -euo pipefail
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-1}
make run NP=${SLURM_NTASKS:-4} N=${N:-128} RE=${RE:-1000} STEPS=${STEPS:-4000} POISSON_ITERS=${POISSON_ITERS:-300} SCHEME=${SCHEME:-upwind}
