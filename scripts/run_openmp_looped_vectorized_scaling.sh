#!/bin/bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON=${PYTHON:-python3}
THREADS_LIST=${THREADS_LIST:-"1 2 4 8 16"}
CASES=${CASES:-"64:100:upwind:1000:200 128:1000:upwind:2000:250"}
REPEATS=${REPEATS:-1}
POISSON_SOLVERS=${POISSON_SOLVERS:-"RBGS RBSOR"}
SOR_OMEGA=${SOR_OMEGA:-1.7}
RESET_RESULTS=${RESET_RESULTS:-1}
CONTINUE_ON_ERROR=${CONTINUE_ON_ERROR:-1}
MAKE_JOBS=${MAKE_JOBS:-1}
PLOTS=${PLOTS:-1}
OUT_DIR="comparison/results/openmp_kernel_scaling"
LOG_DIR="logs/openmp_kernel_scaling"
mkdir -p "$OUT_DIR" "$LOG_DIR"
if [[ "$RESET_RESULTS" == "1" || "$RESET_RESULTS" == "true" ]]; then
    rm -f "$OUT_DIR"/*.csv "$OUT_DIR"/*.md
fi
RUN_LOG="$LOG_DIR/openmp_kernel_scaling_$(date +%Y%m%d_%H%M%S).log"
: > "$RUN_LOG"
log(){ echo "$@" | tee -a "$RUN_LOG"; }

OPENMP_KERNEL_SOLVERS=(
"c_openmp_domain_looped|c/openmp_domain_looped|c|openmp_domain|looped|c/openmp_domain_looped/results/data/c_openmp_domain_looped_summary.csv"
"c_openmp_domain_vectorized|c/openmp_domain_vectorized|c|openmp_domain|vectorized|c/openmp_domain_vectorized/results/data/c_openmp_domain_vectorized_summary.csv"
"cpp_openmp_domain_looped|cpp/openmp_domain_looped|cpp|openmp_domain|looped|cpp/openmp_domain_looped/results/data/cpp_openmp_domain_looped_summary.csv"
"cpp_openmp_domain_vectorized|cpp/openmp_domain_vectorized|cpp|openmp_domain|vectorized|cpp/openmp_domain_vectorized/results/data/cpp_openmp_domain_vectorized_summary.csv"
)

log "OpenMP looped/vectorized scaling"
log "THREADS_LIST=$THREADS_LIST"
log "CASES=$CASES"
log "REPEATS=$REPEATS"

append_row(){
    local solver="$1" lang="$2" model="$3" kernel="$4" summary="$5" case_id="$6" N="$7" RE="$8" scheme="$9" steps="${10}" piters="${11}" threads="${12}" rep="${13}" status="${14}"
    "$PYTHON" scripts/append_strong_scaling_result.py \
        --summary "$summary" --out-dir "$OUT_DIR" \
        --solver-group "$solver" --language "$lang" --parallel-model "$model" --kernel-style "$kernel" \
        --case-id "$case_id" --N "$N" --Re "$RE" --scheme "$scheme" --pressure "NA" \
        --steps "$steps" --poisson-iters "$piters" --mpi-ranks 1 --threads-per-rank "$threads" --total-cores "$threads" \
        --repeat "$rep" --status "$status" --log-file "$RUN_LOG" | tee -a "$RUN_LOG"
}

run_one(){
    local solver="$1" dir="$2" lang="$3" model="$4" kernel="$5" summary="$6" case_id="$7" N="$8" RE="$9" scheme="${10}" steps="${11}" piters="${12}" threads="${13}" rep="${14}"
    rm -f "$summary"
    log ""
    log "===== $solver case=$case_id threads=$threads repeat=$rep ====="
    local rc=0
    OMP_NUM_THREADS="$threads" make -C "$dir" run OMP_NUM_THREADS="$threads" N="$N" RE="$RE" STEPS="$steps" POISSON_ITERS="$piters" SCHEME="$scheme" NO_FIELDS=1 -j"$MAKE_JOBS" 2>&1 | tee -a "$RUN_LOG" || rc=$?
    local status="success"
    if [[ "$rc" != "0" ]]; then status="failed"; log "FAILED: $solver rc=$rc"; fi
    append_row "$solver" "$lang" "$model" "$kernel" "$summary" "$case_id" "$N" "$RE" "$scheme" "$steps" "$piters" "$threads" "$rep" "$status"
    if [[ "$rc" != "0" && "$CONTINUE_ON_ERROR" != "1" && "$CONTINUE_ON_ERROR" != "true" ]]; then exit "$rc"; fi
}

case_index=0
for case_spec in $CASES; do
    case_index=$((case_index+1))
    IFS=':' read -r N RE scheme steps piters <<< "$case_spec"
    case_id="openmp_case${case_index}_N${N}_Re${RE}_${scheme}_steps${steps}_p${piters}"
    for rep in $(seq 1 "$REPEATS"); do
        for entry in "${OPENMP_KERNEL_SOLVERS[@]}"; do
            IFS='|' read -r solver dir lang model kernel summary <<< "$entry"
            for threads in $THREADS_LIST; do
                run_one "$solver" "$dir" "$lang" "$model" "$kernel" "$summary" "$case_id" "$N" "$RE" "$scheme" "$steps" "$piters" "$threads" "$rep"
            done
        done
    done
done

cp "$OUT_DIR/openmp_kernel_scaling_raw.csv" /dev/null 2>/dev/null || true
# The append helper writes strong_scaling_raw.csv by design. Rename for clarity.
if [[ -f "$OUT_DIR/strong_scaling_raw.csv" ]]; then
    cp "$OUT_DIR/strong_scaling_raw.csv" "$OUT_DIR/openmp_kernel_scaling_raw.csv"
fi
"$PYTHON" scripts/compute_strong_scaling.py --raw "$OUT_DIR/strong_scaling_raw.csv" --out-dir "$OUT_DIR" ${PLOTS:+--plots} 2>&1 | tee -a "$RUN_LOG" || true
if [[ -f "$OUT_DIR/strong_scaling_report.md" ]]; then
    cp "$OUT_DIR/strong_scaling_report.md" "$OUT_DIR/openmp_kernel_scaling_report.md"
fi
log "Report: $OUT_DIR/openmp_kernel_scaling_report.md"
