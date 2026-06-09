# C MPI Runner

**Role in the project:** run independent C benchmark cases in parallel with MPI.

This folder builds the C solver and a small MPI case driver. MPI ranks receive different benchmark cases, run them independently, and then the outputs are merged.

This is useful for large parameter studies. It is not a domain-decomposition CFD solver yet.

## Requirements

```text
gcc
mpicc
mpirun
python3
```

Check the machine:

```bash
which mpicc
which mpirun
```

## Build and run

```bash
make build
make smoke NP=2
make quick NP=4
make merge
```

Direct command example:

```bash
mpirun -np 4 bin/mpi_case_driver --mode quick --solver ./bin/lid_cavity_c
python3 tools/merge_mpi_results.py
```

## Output

```text
results/mpi_raw/   raw per-rank outputs
results/data/      merged summary outputs
```

## Notes

- MPI is used here to distribute cases, not grid subdomains.
- This is good for running many Reynolds numbers or mesh sizes faster.
- Use `NP=2`, `NP=4`, or another value suitable for the machine.
