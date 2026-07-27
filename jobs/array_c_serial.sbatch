#!/bin/bash
#SBATCH --job-name=c_serial
#SBATCH --output=logs/c_serial_case_%A_%a.out
#SBATCH --error=logs/c_serial_case_%A_%a.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=20:00:00
#SBATCH --array=1-36%4

bash jobs/run_one_case_isolated.sh c_serial ${SLURM_ARRAY_TASK_ID} 1
