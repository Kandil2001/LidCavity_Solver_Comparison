# Python MPI Runner

**Role in the project:** run independent benchmark cases in parallel using Python and MPI.

This folder distributes cases across MPI ranks. Each rank receives one or more independent cavity cases. This speeds up a parameter study, but it is not a domain-decomposition CFD solver.

## Requirements

```text
python3
mpi4py
mpirun
```

Install Python dependencies:

```bash
make install
```

## Run

```bash
make smoke NP=2
make quick NP=4
```

Direct command example:

```bash
mpirun -np 4 python3 src/mpi_case_driver.py --mode quick --no-fields
```

## Output

```text
results/mpi_raw/   per-rank raw outputs
results/data/      merged summary outputs
```

## Notes

- This is case-level parallelism.
- Use it when you have many independent parameter cases.
- Use the serial Python folder first if you only want to understand the solver.
