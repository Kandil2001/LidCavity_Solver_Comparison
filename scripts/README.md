# Helper Scripts

This folder contains root-level scripts that run several solver folders from one command.

## Scripts

| Script | Purpose |
|---|---|
| `run_smoke_cpu.sh` | Runs small CPU checks and skips missing optional tools |
| `run_quick_cpu.sh` | Runs quick CPU benchmarks and skips missing optional tools |

## Usage

From the repository root:

```bash
make smoke-cpu
make quick-cpu
```

or directly:

```bash
bash scripts/run_smoke_cpu.sh
bash scripts/run_quick_cpu.sh
```

## Notes

- The scripts are written for Linux-style terminals.
- On Windows, WSL is recommended.
- MATLAB, MPI, and CUDA are skipped if the required commands are not available.
