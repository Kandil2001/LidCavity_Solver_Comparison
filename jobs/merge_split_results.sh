#!/bin/bash
set -euo pipefail
cd ~/LidCavity_Solver_Comparison
mkdir -p comparison/results/raw
merge_one() {
    pattern="$1"; out="$2"
    rm -f "$out"
    first=1
    for f in $(ls $pattern 2>/dev/null | sort -V); do
        if [ "$first" -eq 1 ]; then
            cat "$f" > "$out"
            first=0
        else
            tail -n +2 "$f" >> "$out"
        fi
    done
    echo
    echo "===== $out ====="
    if [ -f "$out" ]; then awk 'END{print "Rows:", NR-1}' "$out"; else echo "missing"; fi
}
merge_one "comparison/results/split/c_serial_case_*.csv" "comparison/results/raw/c_serial_full.csv"
merge_one "comparison/results/split/cpp_serial_case_*.csv" "comparison/results/raw/cpp_serial_full.csv"
merge_one "comparison/results/split/c_openmp_t8_case_*.csv" "comparison/results/raw/c_openmp_t8_full.csv"
merge_one "comparison/results/split/cpp_openmp_t8_case_*.csv" "comparison/results/raw/cpp_openmp_t8_full.csv"
merge_one "comparison/results/split/python_vectorized_case_*.csv" "comparison/results/raw/python_serial_vectorized_full.csv"
merge_one "comparison/results/split/python_looped_case_*.csv" "comparison/results/raw/python_serial_looped_full.csv"
merge_one "comparison/results/split/octave_vectorized_case_*.csv" "comparison/results/raw/octave_vectorized_full.csv"
merge_one "comparison/results/split/octave_looped_case_*.csv" "comparison/results/raw/octave_looped_full.csv"
