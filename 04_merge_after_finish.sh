#!/bin/bash
set -euo pipefail
cd ~/LidCavity_Solver_Comparison
if squeue -u "$USER" -h | grep -q .; then
    echo "Jobs are still running. Do not merge yet."
    squeue -u "$USER"
    exit 1
fi
bash jobs/merge_split_results.sh
for f in comparison/results/raw/*.csv; do echo; echo "===== $f ====="; awk 'END{print "Rows:", NR-1}' "$f"; done
