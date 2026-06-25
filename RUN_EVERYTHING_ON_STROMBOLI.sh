#!/bin/bash
set -euo pipefail

# One-command Stromboli runner for Ahmed's LidCavity comparison.
# What it does:
#   1) installs/recreates ~/software/miniforge3/lid_env if missing
#   2) prepares Python 3.10 + Octave + MPI environment
#   3) cleans old outputs inside this repo only
#   4) submits divided Slurm arrays for serial/OpenMP/Python/Octave cases
#   5) submits MPI jobs for C/C++/Python
#   6) submits a dependent final merge/report job

cd "$(dirname "$0")"
REPO="$PWD"

if [ "$(basename "$REPO")" != "LidCavity_Solver_Comparison" ]; then
    echo "ERROR: Please keep the folder name as LidCavity_Solver_Comparison."
    echo "Current folder: $REPO"
    exit 1
fi

mkdir -p logs
MASTER_LOG="logs/RUN_EVERYTHING_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$MASTER_LOG") 2>&1

echo "========================================"
echo "ONE COMMAND RUN: LidCavity Stromboli"
echo "Repo: $REPO"
echo "Start: $(date)"
echo "Log: $MASTER_LOG"
echo "========================================"

# Cancel only previous jobs from this project by job-name patterns.
echo
echo "[1/8] Cancel old LidCavity jobs from this project, if any"
squeue -u "$USER" -h -o "%A %j" | awk '$2 ~ /(c_serial|cpp_serial|c_openmp|cpp_openmp|python_vectorized|python_looped|octave_vectorized|octave_looped|c_mpi_r8_full|cpp_mpi_r8_full|python_mpi_r8_full|lid_|test_one_case|final_merge_report)/ {print $1}' | xargs -r scancel || true
squeue -u "$USER" || true

# Install environment if needed.
echo
echo "[2/8] Set up Python 3.10 + Octave + mpi4py environment"
if [ ! -f "$HOME/software/miniforge3/etc/profile.d/conda.sh" ] || [ ! -x "$HOME/software/miniforge3/envs/lid_env/bin/python" ]; then
    echo "Conda/lid_env missing. Running 00_setup_lid_env.sh"
    bash 00_setup_lid_env.sh
else
    echo "Existing conda/lid_env found. Checking packages."
    source "$HOME/software/miniforge3/etc/profile.d/conda.sh"
    conda activate lid_env
    python --version
    octave --version | head -5 || true
    python -c "import mpi4py; print('mpi4py ok')" || conda install -n lid_env -c conda-forge mpi4py -y
fi

# Clean outputs inside repo only.
echo
echo "[3/8] Clean old outputs inside this repo"
rm -rf logs/*.out logs/*.err logs/final_report_* logs/submitted_jobs.txt 2>/dev/null || true
rm -rf work/* comparison/results/raw/* comparison/results/split/* comparison/results/split/histories/* 2>/dev/null || true
rm -rf c/serial/results/data/* c/openmp/results/data/* c/mpi/results/data/* c/mpi/results/mpi_raw/* 2>/dev/null || true
rm -rf cpp/serial/results/data/* cpp/openmp/results/data/* cpp/mpi/results/data/* cpp/mpi/results/mpi_raw/* 2>/dev/null || true
rm -rf python/serial/results/data/* python/mpi/results/data/* python/mpi/results/mpi_raw/* 2>/dev/null || true
rm -rf matlab/results/data/* 2>/dev/null || true
mkdir -p logs work comparison/results/raw comparison/results/split comparison/results/split/histories
mkdir -p c/serial/results/data c/openmp/results/data c/mpi/results/data c/mpi/results/mpi_raw
mkdir -p cpp/serial/results/data cpp/openmp/results/data cpp/mpi/results/data cpp/mpi/results/mpi_raw
mkdir -p python/serial/results/data python/mpi/results/data python/mpi/results/mpi_raw
mkdir -p matlab/results/data

# Prepare repo scripts and patches.
echo
echo "[4/8] Prepare Stromboli paths and compile/link patches"
bash 01_prepare_stromboli.sh
bash jobs/make_case_array_jobs.sh

# Submit divided array jobs.
echo
echo "[5/8] Submit divided serial/OpenMP/Python/Octave arrays"
jobids=()
for job in \
  jobs/array_c_serial.sbatch \
  jobs/array_cpp_serial.sbatch \
  jobs/array_c_openmp.sbatch \
  jobs/array_cpp_openmp.sbatch \
  jobs/array_python_vectorized.sbatch \
  jobs/array_python_looped.sbatch \
  jobs/array_octave_vectorized.sbatch \
  jobs/array_octave_looped.sbatch
 do
    jid=$(sbatch --parsable "$job")
    jobids+=("$jid")
    echo "$jid  $job"
done

# Create and submit MPI jobs, capturing IDs.
echo
echo "[6/8] Submit C/C++/Python MPI jobs"
cat > jobs/c_mpi_r8_full.sbatch <<'EOT'
#!/bin/bash
#SBATCH --job-name=c_mpi_r8_full
#SBATCH --output=logs/c_mpi_r8_full_%j.out
#SBATCH --error=logs/c_mpi_r8_full_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --time=20:00:00
source jobs/stromboli_data_first_env.sh
make -C c/mpi full NP=8
cp -f c/mpi/results/data/study_summary_mpi.csv comparison/results/raw/c_mpi_r8_full.csv || true
echo "Finished at $(date)"
EOT
cat > jobs/cpp_mpi_r8_full.sbatch <<'EOT'
#!/bin/bash
#SBATCH --job-name=cpp_mpi_r8_full
#SBATCH --output=logs/cpp_mpi_r8_full_%j.out
#SBATCH --error=logs/cpp_mpi_r8_full_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --cpus-per-task=1
#SBATCH --mem=24G
#SBATCH --time=20:00:00
source jobs/stromboli_data_first_env.sh
make -C cpp/mpi full NP=8
cp -f cpp/mpi/results/data/study_summary_mpi.csv comparison/results/raw/cpp_mpi_r8_full.csv || true
echo "Finished at $(date)"
EOT
cat > jobs/python_mpi_r8_full.sbatch <<'EOT'
#!/bin/bash
#SBATCH --job-name=python_mpi_r8_full
#SBATCH --output=logs/python_mpi_r8_full_%j.out
#SBATCH --error=logs/python_mpi_r8_full_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --cpus-per-task=1
#SBATCH --mem=24G
#SBATCH --time=20:00:00
source jobs/stromboli_data_first_env.sh
python3 -c "import mpi4py; print('mpi4py ok')"
make -C python/mpi full NP=8
cp -f python/mpi/results/data/study_summary_mpi.csv comparison/results/raw/python_mpi_r8_full.csv || true
echo "Finished at $(date)"
EOT
for job in jobs/c_mpi_r8_full.sbatch jobs/cpp_mpi_r8_full.sbatch jobs/python_mpi_r8_full.sbatch; do
    jid=$(sbatch --parsable "$job")
    jobids+=("$jid")
    echo "$jid  $job"
done

# Write job list.
printf "%s\n" "${jobids[@]}" > logs/submitted_jobs.txt

dep=$(IFS=:; echo "${jobids[*]}")

# Final dependent merge/report job.
echo
echo "[7/8] Submit dependent final merge/report job"
cat > jobs/final_merge_report.sbatch <<'EOT'
#!/bin/bash
#SBATCH --job-name=final_merge_report
#SBATCH --output=logs/final_merge_report_%j.out
#SBATCH --error=logs/final_merge_report_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=01:00:00

set -euo pipefail
cd ~/LidCavity_Solver_Comparison
source jobs/stromboli_data_first_env.sh

echo "Final merge/report started at $(date)"
echo

echo "Merging split serial/OpenMP/Python/Octave outputs..."
bash jobs/merge_split_results.sh

echo
echo "Raw result counts:"
for f in comparison/results/raw/*.csv; do
    [ -f "$f" ] || continue
    echo
    echo "===== $f ====="
    awk 'END{print "Rows:", NR-1}' "$f"
done

echo
echo "Split CSV count:"
find comparison/results/split -maxdepth 1 -name "*.csv" | wc -l

echo
echo "Error summary:"
grep -iE "error|failed|killed|oom|cannot|undefined|segmentation|traceback|syntax" logs/*.err 2>/dev/null | head -200 || true

echo
echo "Final merge/report finished at $(date)"
EOT
final_jid=$(sbatch --parsable --dependency=afterany:${dep} jobs/final_merge_report.sbatch)
echo "$final_jid  jobs/final_merge_report.sbatch  dependency=afterany:$dep"
echo "$final_jid" > logs/final_merge_job.txt

# Final status.
echo
echo "[8/8] Submitted everything"
echo "Submitted job IDs: ${jobids[*]}"
echo "Final merge job: $final_jid"
echo
echo "Current queue:"
squeue -u "$USER" -o "%.18i %.10P %.25j %.8u %.2t %.10M %.6D %R"
echo
echo "Useful commands:"
echo "  cd ~/LidCavity_Solver_Comparison"
echo "  bash jobs/status.sh"
echo "  squeue -u \$USER"
echo "  cat logs/final_merge_report_${final_jid}.out"
echo "  grep -iE 'error|failed|killed|oom|traceback|syntax' logs/*.err | head -120"
echo
echo "The heavy work is now in Slurm. You can close SSH; the submitted jobs keep running."
echo "The final merge/report job will run automatically after the compute jobs finish."
