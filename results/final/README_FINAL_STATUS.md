# Final CPU + CUDA Result Status

## CPU completeness

### OPENMP
- Cases found: 18
- Total successful raw rows: 2160
- Total failed raw rows: 0
- Missing summaries: 0

### MPI
- Cases found: 18
- Total successful raw rows: 1061
- Total failed raw rows: 2140
- Missing summaries: 0
- Note: case 13 was completed by salvaging successful rows only; failed/time-limited rows remain in the raw file.

### HYBRID
- Cases found: 18
- Total successful raw rows: 1044
- Total failed raw rows: 2100
- Missing summaries: 0
- Note: case 13 was completed by salvaging successful rows only; failed/time-limited rows remain in the raw file.

## CUDA

### New exact CUDA RBGS/RBSOR run
- Rows including header equivalent: 109
- PressureSolver RBGS: 54
- PressureSolver RBSOR: 54
- ValidationPass 0: 108

### Old Jacobi CUDA run
- Rows including header equivalent: 23
- PressureSolver JACOBI: 22

## Recommended usage

- Use OpenMP CPU, salvaged MPI/Hybrid summaries, and the new CUDA RBGS/RBSOR summary for runtime comparison.
- Keep raw failed rows in the audit/completeness table.
- Do not present MPI/Hybrid case 13 as fully clean; present it as partially salvaged from successful rows.
- Do not present CUDA validation as passed; all 108 rows in the new RBGS/RBSOR run have ValidationPass = 0.

