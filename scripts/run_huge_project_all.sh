#!/bin/bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"
mkdir -p logs comparison/results/mega_project

PYTHON=${PYTHON:-python3}
CASES=${CASES:-"$($PYTHON scripts/full_case_list.py --domain | tr '\n' ' ')"}
REPEATS=${REPEATS:-1}
RANKS=${RANKS:-"1 2 4 8 16"}
THREADS_LIST=${THREADS_LIST:-"1 2 4 8 16"}
HYBRID_PAIRS=${HYBRID_PAIRS:-"1x1 1x2 2x2 4x2 4x4"}
RUN_DOMAIN_SCALING=${RUN_DOMAIN_SCALING:-1}
RUN_REPORT=${RUN_REPORT:-1}

echo "Huge project direct runner"
echo "This runs the new domain-decomposition strong-scaling matrix directly in the current shell."
echo "For the original full benchmark arrays, use: bash jobs/submit_huge_project_all.sh"
echo "CASES=$CASES"

if [[ "$RUN_DOMAIN_SCALING" == "1" || "$RUN_DOMAIN_SCALING" == "true" ]]; then
    CASES="$CASES" REPEATS="$REPEATS" RANKS="$RANKS" THREADS_LIST="$THREADS_LIST" HYBRID_PAIRS="$HYBRID_PAIRS" \
        bash scripts/run_strong_scaling_all.sh
fi

if [[ "$RUN_REPORT" == "1" || "$RUN_REPORT" == "true" ]]; then
    $PYTHON scripts/mega_project_report.py
    echo "Report: comparison/results/mega_project/mega_project_report.md"
fi
