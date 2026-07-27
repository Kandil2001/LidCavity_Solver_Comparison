#!/bin/bash
#SBATCH --job-name=python_mpi_safe
#SBATCH --output=logs/python_mpi_safe_%A_%a.out
#SBATCH --error=logs/python_mpi_safe_%A_%a.err
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --time=1-00:00:00
#SBATCH --array=1-18%2

set -e

source jobs/stromboli_data_first_env.sh

cd "$SLURM_SUBMIT_DIR/python/mpi"

chunk_size=4
start=$(( (SLURM_ARRAY_TASK_ID - 1) * chunk_size + 1 ))
end=$(( SLURM_ARRAY_TASK_ID * chunk_size ))

echo "Python MPI safe chunk"
echo "Array task: $SLURM_ARRAY_TASK_ID"
echo "Cases: $start to $end"
echo "Node: $(hostname)"
echo "Python: $(which python3)"
python3 --version
echo "mpirun: $(which mpirun)"

mpirun -np 4 python3 src/mpi_case_driver.py \
    --mode full \
    --no-fields \
    --case-start "$start" \
    --case-end "$end" \
    --part "$SLURM_ARRAY_TASK_ID"

echo "Finished safe Python MPI chunk $SLURM_ARRAY_TASK_ID at $(date)"
