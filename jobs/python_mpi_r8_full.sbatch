#!/bin/bash
#SBATCH --job-name=python_mpi_r8
#SBATCH --output=logs/python_mpi_r8_%j.out
#SBATCH --error=logs/python_mpi_r8_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --cpus-per-task=1
#SBATCH --time=24:00:00

source jobs/stromboli_data_first_env.sh

echo "Python:"
which python3
python3 --version

echo "MPI:"
which mpirun || true
python3 -c "import mpi4py; print('mpi4py ok')"

echo "Starting Python MPI at $(date)"

make -C python/mpi full NP=8

mkdir -p comparison/results/raw
cp -f python/mpi/results/data/study_summary_mpi.csv comparison/results/raw/python_mpi_r8_full.csv || true

echo "Finished Python MPI at $(date)"
