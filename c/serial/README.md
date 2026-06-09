# C serial solver

This is the low-level CPU baseline. It keeps the same benchmark setup as the MATLAB and Python versions, but with explicit memory layout and plain loops.

## Build and run

```bash
make build
make smoke
make quick
make run N=128 RE=400 SCHEME=upwind PRESSURE=RBGS
make plot
```

Outputs are written to `results/data/` and `results/figures/`.
