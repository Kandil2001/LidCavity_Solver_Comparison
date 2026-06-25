#!/bin/bash
set -euo pipefail
mkdir -p jobs logs
make_array_job() {
    solver="$1"; cpus="$2"; mem="$3"; time="$4"; threads="$5"; limit="$6"
    job="jobs/array_${solver}.sbatch"
    cat > "$job" <<EOT
#!/bin/bash
#SBATCH --job-name=${solver}
#SBATCH --output=logs/${solver}_case_%A_%a.out
#SBATCH --error=logs/${solver}_case_%A_%a.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=${cpus}
#SBATCH --mem=${mem}
#SBATCH --time=${time}
#SBATCH --array=1-36%${limit}

bash jobs/run_one_case_isolated.sh ${solver} \${SLURM_ARRAY_TASK_ID} ${threads}
EOT
    echo "$job"
}
make_array_job c_serial           1  8G 20:00:00 1 4
make_array_job cpp_serial         1 16G 20:00:00 1 4
make_array_job c_openmp           8 16G 20:00:00 8 2
make_array_job cpp_openmp         8 24G 20:00:00 8 2
make_array_job python_vectorized  1 16G 20:00:00 1 3
make_array_job python_looped      1 16G 20:00:00 1 2
make_array_job octave_vectorized  1 16G 20:00:00 1 2
make_array_job octave_looped      1 16G 20:00:00 1 1
