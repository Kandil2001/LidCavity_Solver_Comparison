#!/bin/bash
cd ~/LidCavity_Solver_Comparison

echo
echo "===== MPI QUEUE ====="
squeue -u $USER -o "%.18i %.30j %.2t %.12M %.12l %R" | grep -i mpi || echo "No MPI jobs in queue"

echo
echo "===== C / C++ MPI RESULTS ====="
for f in comparison/results/raw/c_mpi_r8_full.csv comparison/results/raw/cpp_mpi_r8_full.csv c/mpi/results/data/study_summary_mpi.csv cpp/mpi/results/data/study_summary_mpi.csv
do
    if [ -f "$f" ]; then
        echo "$f"
        awk 'END{print "Rows:", NR-1}' "$f"
    fi
done

echo
echo "===== PYTHON MPI PART RESULTS ====="
for f in python/mpi/results/data/study_summary_mpi_part_*.csv
do
    [ -f "$f" ] || continue
    case "$f" in
        *rank*) continue ;;
    esac
    echo "$f"
    awk 'END{print "Rows:", NR-1}' "$f"
done

echo
echo "===== PYTHON MPI CASE IDS FINISHED ====="
found=$(find python/mpi/results/data -name "study_summary_mpi_part_*.csv" ! -name "*rank*" -print0 2>/dev/null \
| xargs -0 awk -F, 'FNR>1 {print $1}' 2>/dev/null \
| grep -E '^[0-9]+$' \
| sort -n | uniq)

echo "$found" | tr '\n' ' '
echo

echo
echo "===== PYTHON MPI CASE IDS MISSING FROM 1..72 ====="
comm -23 <(seq 1 72) <(echo "$found") | tr '\n' ' '
echo

echo
echo "===== MPI ERRORS, NEW SAFE JOBS ONLY ====="
grep -iE "error|failed|killed|oom|cannot|undefined|segmentation|traceback|syntax|timeout|time limit|no such file" logs/*mpi_safe*.err logs/*mpi_r8_safe*.err 2>/dev/null || echo "No new safe MPI errors found"
