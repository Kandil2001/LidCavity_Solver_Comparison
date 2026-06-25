#!/bin/bash
#SBATCH --job-name=cpp_serial
#SBATCH --output=logs/cpp_serial_case_%A_%a.out
#SBATCH --error=logs/cpp_serial_case_%A_%a.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=20:00:00
#SBATCH --array=1-36%4

bash jobs/run_one_case_isolated.sh cpp_serial ${SLURM_ARRAY_TASK_ID} 1
