# Python serial solver

This is the readable Python / NumPy implementation. It is useful for checking the numerical workflow and for writing post-processing scripts before moving to C or C++.

## Setup

```bash
make install
```

## Run

```bash
make smoke
make quick
make run N=128 RE=400 SCHEME=upwind PRESSURE=RBGS
make plot
```

Outputs are written to `results/data/` and `results/figures/`.
