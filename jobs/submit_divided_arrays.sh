#!/bin/bash
set -euo pipefail
cd ~/LidCavity_Solver_Comparison
bash jobs/make_case_array_jobs.sh
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
    echo "$jid  $job"
done
squeue -u "$USER" -o "%.18i %.10P %.25j %.8u %.2t %.10M %.6D %R"
