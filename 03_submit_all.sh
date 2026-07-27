#!/bin/bash
set -euo pipefail
cd ~/LidCavity_Solver_Comparison
bash jobs/submit_divided_arrays.sh
bash jobs/submit_mpi_jobs.sh
