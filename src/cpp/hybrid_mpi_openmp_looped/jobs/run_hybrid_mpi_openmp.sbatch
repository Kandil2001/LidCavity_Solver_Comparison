#!/bin/bash
#SBATCH --job-name=hybrid_lid
#SBATCH --output=results/logs/hybrid_lid_%j.out
#SBATCH --error=results/logs/hybrid_lid_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=02:00:00

set -euo pipefail

cd "$SLURM_SUBMIT_DIR"

module load openmpi >/dev/null 2>&1 || true
module load mpi >/dev/null 2>&1 || true

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export OMP_PROC_BIND=close
export OMP_PLACES=cores

make build
mpirun -np ${SLURM_NTASKS:-4} ./bin/hybrid_lid_cavity \
    --N 128 \
    --Re 1000 \
    --steps 4000 \
    --poisson-iters 300 \
    --scheme upwind \
    --output-every 200
