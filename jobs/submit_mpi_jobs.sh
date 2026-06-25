#!/bin/bash
set -euo pipefail
cd ~/LidCavity_Solver_Comparison
mkdir -p logs comparison/results/raw
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
jid1=$(sbatch --parsable jobs/c_mpi_r8_full.sbatch)
jid2=$(sbatch --parsable jobs/cpp_mpi_r8_full.sbatch)
jid3=$(sbatch --parsable jobs/python_mpi_r8_full.sbatch)
echo "C MPI:      $jid1"
echo "C++ MPI:    $jid2"
echo "Python MPI: $jid3"
squeue -u "$USER" -o "%.18i %.10P %.25j %.8u %.2t %.10M %.6D %R"
