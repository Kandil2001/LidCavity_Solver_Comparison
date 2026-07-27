#!/bin/bash
#SBATCH --job-name=lid_hybrid_3rep
#SBATCH --partition=compute2011
#SBATCH --output=logs/arrays/hybrid_%A_%a.out
#SBATCH --error=logs/arrays/hybrid_%A_%a.err
#SBATCH --array=1-18
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=4
#SBATCH --time=96:00:00
#SBATCH --mem=16G

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$PWD}"

module purge
module load mpi/openmpi/4.1.8

source ~/venvs/lidcavity_py38/bin/activate

export MPI_HOME=/cluster/mpi/openmpi/4.1.8
export PATH=$MPI_HOME/bin:$PATH
export LD_LIBRARY_PATH=$MPI_HOME/lib:/cluster/tools/anaconda3/2021.05/lib:$LD_LIBRARY_PATH

export OMPI_MCA_pml=ob1
export OMPI_MCA_btl=self,vader,tcp
export OMPI_MCA_btl_openib_allow_ib=0

export PYTHON=$(which python)

CASE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" case_list_domain.txt)

RUN_MPI=0 RUN_HYBRID=1 RUN_OPENMP=0 \
RUN_ORIGINAL_FULL=0 RUN_ORIGINAL_OPENMP_CONTEXT=0 \
OUT_DIR="comparison/results/strong_scaling_parts/hybrid_case_${SLURM_ARRAY_TASK_ID}" \
LOG_DIR="logs/strong_scaling_parts/hybrid_case_${SLURM_ARRAY_TASK_ID}" \
CASES="$CASE" \
POISSON_SOLVERS="RBGS RBSOR" \
SOR_OMEGA=1.7 \
REPEATS=3 \
HYBRID_PAIRS="1x1 1x2 2x2 4x2 4x4" \
RESET_RESULTS=1 \
PLOTS=0 \
bash scripts/run_strong_scaling_all.sh
