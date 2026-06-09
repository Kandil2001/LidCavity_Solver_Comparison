# C++ serial solver

This is the structured compiled-code baseline. It keeps the solver readable while using C++ containers and a cleaner application layout.

## Build and run

```bash
make build
make smoke
make quick
make run N=128 RE=400 SCHEME=upwind PRESSURE=RBGS
make plot
```

Outputs are written to `results/data/` and `results/figures/`.
