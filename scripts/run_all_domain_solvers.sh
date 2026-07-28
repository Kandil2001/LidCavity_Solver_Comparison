#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cat <<'EOF'
run_all_domain_solvers.sh now delegates to the canonical organized domain-solver matrix.

This executes the looped and vectorized MPI/hybrid implementations under src/ for C, C++, and Python. It is a fixed-step execution workflow, not a convergence-controlled paper benchmark.
EOF

exec bash "$SCRIPT_DIR/run_domain_kernel_matrix.sh"
