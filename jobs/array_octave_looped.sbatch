#!/bin/bash
#SBATCH --job-name=octave_looped
#SBATCH --output=logs/octave_looped_case_%A_%a.out
#SBATCH --error=logs/octave_looped_case_%A_%a.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=20:00:00
#SBATCH --array=1-36%1

bash jobs/run_one_case_isolated.sh octave_looped ${SLURM_ARRAY_TASK_ID} 1
