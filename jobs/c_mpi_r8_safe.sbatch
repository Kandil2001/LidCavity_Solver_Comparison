#!/bin/bash
#SBATCH --job-name=c_mpi_r8_safe
#SBATCH --output=logs/c_mpi_r8_safe_%j.out
#SBATCH --error=logs/c_mpi_r8_safe_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --cpus-per-task=1
#SBATCH --time=1-00:00:00

set -e

source jobs/stromboli_data_first_env.sh

echo "Starting C MPI at $(date)"
echo "Node: $(hostname)"
echo "mpirun: $(which mpirun)"

make -C c/mpi clean 2>/dev/null || true
make -C c/mpi full NP=8

mkdir -p comparison/results/raw
cp -f c/mpi/results/data/study_summary_mpi.csv comparison/results/raw/c_mpi_r8_full.csv

echo "Finished C MPI at $(date)"
awk 'END{print "Rows:", NR-1}' comparison/results/raw/c_mpi_r8_full.csv
