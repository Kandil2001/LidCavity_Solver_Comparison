#!/bin/bash
#SBATCH --job-name=cpp_phys_fields
#SBATCH --output=logs/cpp_phys_fields_%A_%a.out
#SBATCH --error=logs/cpp_phys_fields_%A_%a.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=1-00:00:00
#SBATCH --array=1-4%1

set -e

source jobs/stromboli_data_first_env.sh

cd "$SLURM_SUBMIT_DIR"

export OMP_NUM_THREADS=4

case "$SLURM_ARRAY_TASK_ID" in
    1)
        N=64
        RE=100
        ;;
    2)
        N=64
        RE=400
        ;;
    3)
        N=64
        RE=1000
        ;;
    4)
        N=128
        RE=1000
        ;;
esac

echo "Running physics field case"
echo "N=$N"
echo "Re=$RE"
echo "Scheme=central"
echo "Pressure=RBSOR"
echo "Threads=$OMP_NUM_THREADS"
echo "Node=$(hostname)"
echo "Start=$(date)"

make -C cpp/openmp build

cd cpp/openmp

OMP_NUM_THREADS=4 ./bin/lid_cavity_openmp \
    --single \
    --N "$N" \
    --Re "$RE" \
    --scheme central \
    --pressure RBSOR \
    --implementation openmp_cpp

echo "Finished solver at $(date)"

python3 postprocess/plot_results.py --all-cases --summaries all

echo "Finished plotting at $(date)"
