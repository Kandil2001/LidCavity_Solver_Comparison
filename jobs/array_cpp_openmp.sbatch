#!/bin/bash
#SBATCH --job-name=cpp_openmp
#SBATCH --output=logs/cpp_openmp_case_%A_%a.out
#SBATCH --error=logs/cpp_openmp_case_%A_%a.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=20:00:00
#SBATCH --array=1-36%2

bash jobs/run_one_case_isolated.sh cpp_openmp ${SLURM_ARRAY_TASK_ID} 4
