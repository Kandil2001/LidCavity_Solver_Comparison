#!/bin/bash
#SBATCH --job-name=python_vectorized
#SBATCH --output=logs/python_vectorized_case_%A_%a.out
#SBATCH --error=logs/python_vectorized_case_%A_%a.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=20:00:00
#SBATCH --array=1-36%3

bash jobs/run_one_case_isolated.sh python_vectorized ${SLURM_ARRAY_TASK_ID} 1
