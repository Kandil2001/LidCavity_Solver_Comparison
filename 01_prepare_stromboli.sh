#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p logs work comparison/results/raw comparison/results/split comparison/results/split/histories
mkdir -p c/serial/results/data c/openmp/results/data c/mpi/results/data c/mpi/results/mpi_raw
mkdir -p cpp/serial/results/data cpp/openmp/results/data cpp/mpi/results/data cpp/mpi/results/mpi_raw
mkdir -p python/serial/results/data python/mpi/results/data python/mpi/results/mpi_raw
mkdir -p matlab/results/data
mkdir -p jobs/python_new/bin

if [ -f "$HOME/software/miniforge3/envs/lid_env/bin/python" ]; then
    ln -sf "$HOME/software/miniforge3/envs/lid_env/bin/python" jobs/python_new/bin/python3
    ln -sf "$HOME/software/miniforge3/envs/lid_env/bin/python" jobs/python_new/bin/python
else
    echo "Missing $HOME/software/miniforge3/envs/lid_env/bin/python"
    echo "Run: bash 00_setup_lid_env.sh"
    exit 1
fi

for f in cpp/serial/Makefile cpp/openmp/Makefile cpp/mpi/Makefile; do
    sed -i '/lid_cavity\.cpp/ {/stdc++fs/! s|$| -lstdc++fs|}' "$f"
done

cat > jobs/stromboli_data_first_env.sh <<'ENVEOF'
#!/bin/bash
cd ~/LidCavity_Solver_Comparison

export RUN_CUDA=0
export LIDCAVITY_NO_FIGURES=1
export LIDCAVITY_NO_FIELDS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export OMP_PROC_BIND=close
export OMP_PLACES=cores

source /etc/profile.d/modules.sh 2>/dev/null || true
module load openmpi >/dev/null 2>&1 || true
module load mpi >/dev/null 2>&1 || true

if [ -d /cluster/mpi/openmpi/4.1.8/bin ]; then
    export PATH=/cluster/mpi/openmpi/4.1.8/bin:$PATH
    export LD_LIBRARY_PATH=/cluster/mpi/openmpi/4.1.8/lib:${LD_LIBRARY_PATH:-}
fi

if [ -f "$HOME/software/miniforge3/etc/profile.d/conda.sh" ]; then
    source "$HOME/software/miniforge3/etc/profile.d/conda.sh"
    conda activate lid_env
fi

export PATH="$PWD/jobs/python_new/bin:$PATH"

export RUN_ROOT="$PWD"

echo "========================================"
echo "Node: $(hostname)"
echo "Job: ${SLURM_JOB_ID:-no_slurm_id}"
echo "Array task: ${SLURM_ARRAY_TASK_ID:-no_array_task}"
echo "Start: $(date)"
echo "CUDA disabled, figures disabled, field dumps disabled"
echo "========================================"
which python3 || true
python3 --version || true
which octave || true
octave --version | head -5 || true
which mpirun || true
echo "========================================"
ENVEOF
chmod +x jobs/stromboli_data_first_env.sh

echo "Prepared project."
grep -n "stdc++fs" cpp/serial/Makefile cpp/openmp/Makefile cpp/mpi/Makefile || true
