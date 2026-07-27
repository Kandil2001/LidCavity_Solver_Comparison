#!/bin/bash
#SBATCH --job-name=mpi_domain_lid
#SBATCH --output=results/logs/mpi_domain_%j.out
#SBATCH --error=results/logs/mpi_domain_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --time=02:00:00
#SBATCH --mem=8G

set -e
cd "$SLURM_SUBMIT_DIR"

make build
mpirun -np ${SLURM_NTASKS:-4} ./bin/mpi_domain_lid_cavity \
    --N 128 \
    --Re 1000 \
    --steps 4000 \
    --poisson-iters 300 \
    --output-every 200 \
    --scheme upwind
