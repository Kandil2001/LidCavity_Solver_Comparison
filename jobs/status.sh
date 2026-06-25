#!/bin/bash
cd ~/LidCavity_Solver_Comparison
squeue -u "$USER" -o "%.18i %.10P %.25j %.8u %.2t %.10M %.6D %R"
echo
echo "Split CSV files: $(find comparison/results/split -maxdepth 1 -name '*.csv' 2>/dev/null | wc -l) / 288 expected"
echo
echo "Recent errors:"
grep -iE "error|failed|killed|oom|cannot|undefined|segmentation|traceback|syntax" logs/*.err 2>/dev/null | head -80 || true
