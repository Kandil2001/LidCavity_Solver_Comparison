#!/usr/bin/env bash
# Submit a full, data-first, no-CUDA Stromboli study.
#
# This script is safe to run on the login/front-end node because it only writes
# Slurm job files and calls sbatch. Solver work runs inside Slurm allocations.
set -euo pipefail

ROOT="$HOME/LidCavity_Solver_Comparison"
if [ ! -d "$ROOT" ]; then
    echo "Repo not found at $ROOT" >&2
    echo "Edit ROOT inside this script or cd/unzip the repo to ~/LidCavity_Solver_Comparison." >&2
    exit 1
fi
cd "$ROOT"
mkdir -p jobs logs comparison/results/raw comparison/results/data_first

cat > jobs/stromboli_data_first_env.sh <<'ENV'
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

if [ -f /etc/profile.d/modules.sh ]; then
    source /etc/profile.d/modules.sh || true
fi

if type module >/dev/null 2>&1; then
    module load octave >/dev/null 2>&1 || true
    module load openmpi >/dev/null 2>&1 || true
    module load mpi >/dev/null 2>&1 || true
fi

if [ -d /cluster/mpi/openmpi/4.1.8/bin ]; then
    export PATH=/cluster/mpi/openmpi/4.1.8/bin:$PATH
    export LD_LIBRARY_PATH=/cluster/mpi/openmpi/4.1.8/lib:${LD_LIBRARY_PATH:-}
fi

echo "========================================"
echo "Node: $(hostname)"
echo "Job: ${SLURM_JOB_ID:-no_slurm_id}"
echo "Start: $(date)"
echo "CUDA: disabled"
echo "Figures: disabled"
echo "Field CSV dumps: disabled"
echo "Residual histories + summaries: enabled"
echo "========================================"
echo "Tool check:"
which gcc || true
which g++ || true
which python3 || true
which octave || true
which mpicc || true
which mpicxx || true
which mpirun || true
echo "========================================"
ENV
chmod +x jobs/stromboli_data_first_env.sh

cat > jobs/full_matlab_octave_data.sbatch <<'EOF'
#!/bin/bash
#SBATCH --job-name=lid_mat_full_data
#SBATCH --output=logs/lid_mat_full_data_%j.out
#SBATCH --error=logs/lid_mat_full_data_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=24:00:00

source jobs/stromboli_data_first_env.sh
if command -v octave >/dev/null 2>&1; then
    ENGINE=octave make -C matlab full
    cp -f matlab/results/data/study_summary_full_matlab.csv comparison/results/raw/matlab_octave_serial_full.csv || true
else
    echo "Octave not found; MATLAB/Octave full study skipped."
fi
echo "Finished at $(date)"
EOF

cat > jobs/full_python_serial_data.sbatch <<'EOF'
#!/bin/bash
#SBATCH --job-name=lid_py_full_data
#SBATCH --output=logs/lid_py_full_data_%j.out
#SBATCH --error=logs/lid_py_full_data_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --time=24:00:00

source jobs/stromboli_data_first_env.sh
make -C python/serial full NO_FIELDS=1
cp -f python/serial/results/data/study_summary_full.csv comparison/results/raw/python_serial_full.csv || true
echo "Finished at $(date)"
EOF

cat > jobs/full_c_serial_data.sbatch <<'EOF'
#!/bin/bash
#SBATCH --job-name=lid_c_full_data
#SBATCH --output=logs/lid_c_full_data_%j.out
#SBATCH --error=logs/lid_c_full_data_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=12:00:00

source jobs/stromboli_data_first_env.sh
make -C c/serial full NO_FIELDS=1
cp -f c/serial/results/data/study_summary_full.csv comparison/results/raw/c_serial_full.csv || true
echo "Finished at $(date)"
EOF

cat > jobs/full_cpp_serial_data.sbatch <<'EOF'
#!/bin/bash
#SBATCH --job-name=lid_cpp_full_data
#SBATCH --output=logs/lid_cpp_full_data_%j.out
#SBATCH --error=logs/lid_cpp_full_data_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=12:00:00

source jobs/stromboli_data_first_env.sh
make -C cpp/serial full NO_FIELDS=1
cp -f cpp/serial/results/data/study_summary_full.csv comparison/results/raw/cpp_serial_full.csv || true
echo "Finished at $(date)"
EOF

cat > jobs/full_c_openmp_data.sbatch <<'EOF'
#!/bin/bash
#SBATCH --job-name=lid_c_omp_full_data
#SBATCH --output=logs/lid_c_omp_full_data_%j.out
#SBATCH --error=logs/lid_c_omp_full_data_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=24:00:00

source jobs/stromboli_data_first_env.sh
for t in 1 2 4 8; do
    echo "C OpenMP full study with $t threads"
    export OMP_NUM_THREADS=$t
    make -C c/openmp full OMP_NUM_THREADS=$t NO_FIELDS=1
    cp -f c/openmp/results/data/study_summary_full.csv "comparison/results/raw/c_openmp_threads${t}_full.csv" || true
done
echo "Finished at $(date)"
EOF

cat > jobs/full_cpp_openmp_data.sbatch <<'EOF'
#!/bin/bash
#SBATCH --job-name=lid_cpp_omp_full_data
#SBATCH --output=logs/lid_cpp_omp_full_data_%j.out
#SBATCH --error=logs/lid_cpp_omp_full_data_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=24:00:00

source jobs/stromboli_data_first_env.sh
for t in 1 2 4 8; do
    echo "C++ OpenMP full study with $t threads"
    export OMP_NUM_THREADS=$t
    make -C cpp/openmp full OMP_NUM_THREADS=$t NO_FIELDS=1
    cp -f cpp/openmp/results/data/study_summary_full.csv "comparison/results/raw/cpp_openmp_threads${t}_full.csv" || true
done
echo "Finished at $(date)"
EOF

cat > jobs/full_c_mpi_data.sbatch <<'EOF'
#!/bin/bash
#SBATCH --job-name=lid_c_mpi_full_data
#SBATCH --output=logs/lid_c_mpi_full_data_%j.out
#SBATCH --error=logs/lid_c_mpi_full_data_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --time=24:00:00

source jobs/stromboli_data_first_env.sh
if command -v mpirun >/dev/null 2>&1 && command -v mpicc >/dev/null 2>&1; then
    for r in 1 2 4 8; do
        echo "C MPI full study with $r ranks"
        make -C c/mpi full NP=$r
        cp -f c/mpi/results/data/study_summary_mpi.csv "comparison/results/raw/c_mpi_ranks${r}_full.csv" || true
    done
else
    echo "MPI not available; skipping C MPI full study."
fi
echo "Finished at $(date)"
EOF

cat > jobs/full_cpp_mpi_data.sbatch <<'EOF'
#!/bin/bash
#SBATCH --job-name=lid_cpp_mpi_full_data
#SBATCH --output=logs/lid_cpp_mpi_full_data_%j.out
#SBATCH --error=logs/lid_cpp_mpi_full_data_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --time=24:00:00

source jobs/stromboli_data_first_env.sh
if command -v mpirun >/dev/null 2>&1 && command -v mpicc >/dev/null 2>&1; then
    for r in 1 2 4 8; do
        echo "C++ MPI full study with $r ranks"
        make -C cpp/mpi full NP=$r
        cp -f cpp/mpi/results/data/study_summary_mpi.csv "comparison/results/raw/cpp_mpi_ranks${r}_full.csv" || true
    done
else
    echo "MPI not available; skipping C++ MPI full study."
fi
echo "Finished at $(date)"
EOF

cat > jobs/full_python_mpi_data.sbatch <<'EOF'
#!/bin/bash
#SBATCH --job-name=lid_py_mpi_full_data
#SBATCH --output=logs/lid_py_mpi_full_data_%j.out
#SBATCH --error=logs/lid_py_mpi_full_data_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --cpus-per-task=1
#SBATCH --mem=24G
#SBATCH --time=24:00:00

source jobs/stromboli_data_first_env.sh
if command -v mpirun >/dev/null 2>&1; then
    for r in 1 2 4 8; do
        echo "Python MPI full study with $r ranks"
        make -C python/mpi full NP=$r
        cp -f python/mpi/results/data/study_summary_mpi.csv "comparison/results/raw/python_mpi_ranks${r}_full.csv" || true
    done
else
    echo "MPI not available; skipping Python MPI full study."
fi
echo "Finished at $(date)"
EOF

cat > jobs/full_data_postprocess.sbatch <<'EOF'
#!/bin/bash
#SBATCH --job-name=lid_full_data_post
#SBATCH --output=logs/lid_full_data_post_%j.out
#SBATCH --error=logs/lid_full_data_post_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=04:00:00

source jobs/stromboli_data_first_env.sh
python3 scripts/aggregate_full_study_data.py --mode full

echo "Generated data-first comparison files:"
find comparison/results/data_first -maxdepth 1 -type f | sort
echo "Finished at $(date)"
EOF

echo "Submitting full data-first no-CUDA study."
echo "This creates summaries/residual data only; no images and no field CSV dumps."

jid1=$(sbatch --parsable jobs/full_matlab_octave_data.sbatch)
jid2=$(sbatch --parsable jobs/full_python_serial_data.sbatch)
jid3=$(sbatch --parsable jobs/full_c_serial_data.sbatch)
jid4=$(sbatch --parsable jobs/full_cpp_serial_data.sbatch)
jid5=$(sbatch --parsable jobs/full_c_openmp_data.sbatch)
jid6=$(sbatch --parsable jobs/full_cpp_openmp_data.sbatch)
jid7=$(sbatch --parsable jobs/full_c_mpi_data.sbatch)
jid8=$(sbatch --parsable jobs/full_cpp_mpi_data.sbatch)
jid9=$(sbatch --parsable jobs/full_python_mpi_data.sbatch)

deps="${jid1}:${jid2}:${jid3}:${jid4}:${jid5}:${jid6}:${jid7}:${jid8}:${jid9}"
jid10=$(sbatch --parsable --dependency=afterany:$deps jobs/full_data_postprocess.sbatch)

echo
echo "Submitted:"
echo "  MATLAB/Octave serial full: $jid1"
echo "  Python serial full:        $jid2"
echo "  C serial full:             $jid3"
echo "  C++ serial full:           $jid4"
echo "  C OpenMP full x 1,2,4,8:   $jid5"
echo "  C++ OpenMP full x 1,2,4,8: $jid6"
echo "  C MPI full x 1,2,4,8:      $jid7"
echo "  C++ MPI full x 1,2,4,8:    $jid8"
echo "  Python MPI full x 1,2,4,8: $jid9"
echo "  Data aggregation:          $jid10"
echo
echo "Check queue:"
echo "  squeue -u \$USER"
echo
echo "Watch logs:"
echo "  tail -f logs/lid_*_data_*.out logs/lid_full_data_post_*.out"
