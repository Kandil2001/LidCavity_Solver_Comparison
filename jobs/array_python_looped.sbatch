#!/bin/bash
#SBATCH --job-name=python_looped
#SBATCH --output=logs/python_looped_case_%A_%a.out
#SBATCH --error=logs/python_looped_case_%A_%a.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=20:00:00
#SBATCH --array=1-36%2

bash jobs/run_one_case_isolated.sh python_looped ${SLURM_ARRAY_TASK_ID} 1
