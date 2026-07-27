#!/bin/bash
#SBATCH --job-name=python_mpi_chunk
#SBATCH --output=logs/python_mpi_chunk_%A_%a.out
#SBATCH --error=logs/python_mpi_chunk_%A_%a.err
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --cpus-per-task=1
#SBATCH --time=1-00:00:00
#SBATCH --array=1-9%2

set -e

source jobs/stromboli_data_first_env.sh

cd "$SLURM_SUBMIT_DIR/python/mpi"

chunk_size=8
start=$(( (SLURM_ARRAY_TASK_ID - 1) * chunk_size + 1 ))
end=$(( SLURM_ARRAY_TASK_ID * chunk_size ))

echo "Python MPI chunk job"
echo "Array task: $SLURM_ARRAY_TASK_ID"
echo "Cases: $start to $end"
echo "Node: $(hostname)"
echo "Python: $(which python3)"
python3 --version
echo "mpirun: $(which mpirun)"

mpirun -np 8 python3 src/mpi_case_driver.py \
    --mode full \
    --no-fields \
    --case-start "$start" \
    --case-end "$end" \
    --part "$SLURM_ARRAY_TASK_ID"

echo "Finished chunk $SLURM_ARRAY_TASK_ID at $(date)"
