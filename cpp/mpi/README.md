# C++ MPI Runner

**Role in the project:** run independent C++ benchmark cases in parallel with MPI.

This folder builds the C++ solver and a small MPI case driver. MPI ranks receive different benchmark cases, run them independently, and then the outputs are merged.

This is useful for large parameter studies. It is not a domain-decomposition CFD solver yet.

## Requirements

```text
g++
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
mpirun -np 4 bin/mpi_case_driver --mode quick --solver ./bin/lid_cavity
python3 tools/merge_mpi_results.py
```

## Output

```text
results/mpi_raw/   raw per-rank outputs
results/data/      merged summary outputs
```

## Notes

- MPI is used here for case-level parallelism.
- It is useful when many independent cases need to be run.
- Domain decomposition can be added later as a separate development step.
