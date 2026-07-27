#!/bin/bash
#SBATCH --job-name=cpp_mpi_r8_safe
#SBATCH --output=logs/cpp_mpi_r8_safe_%j.out
#SBATCH --error=logs/cpp_mpi_r8_safe_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --cpus-per-task=1
#SBATCH --time=1-00:00:00

set -e

source jobs/stromboli_data_first_env.sh

echo "Starting C++ MPI at $(date)"
echo "Node: $(hostname)"
echo "mpirun: $(which mpirun)"

# Make C++ compilation lighter and GCC8-compatible
sed -i 's/-O3/-O2/g' cpp/mpi/Makefile
sed -i 's/-march=native//g' cpp/mpi/Makefile
grep -q -- "-lstdc++fs" cpp/mpi/Makefile || sed -i 's|$(CXX) $(CXXFLAGS) src/lid_cavity.cpp -o $(SOLVER)|$(CXX) $(CXXFLAGS) src/lid_cavity.cpp -o $(SOLVER) -lstdc++fs|g' cpp/mpi/Makefile

make -C cpp/mpi clean 2>/dev/null || true
make -C cpp/mpi full NP=8

mkdir -p comparison/results/raw
cp -f cpp/mpi/results/data/study_summary_mpi.csv comparison/results/raw/cpp_mpi_r8_full.csv

echo "Finished C++ MPI at $(date)"
awk 'END{print "Rows:", NR-1}' comparison/results/raw/cpp_mpi_r8_full.csv
