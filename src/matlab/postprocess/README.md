# MATLAB post-processing entry point

MATLAB plotting functions live in `src/postprocess/` because they are part of the MATLAB solver workflow.

Use this command from the `matlab/` folder after a run:

```bash
make plots
```

Generated figures are written to `results/figures/`.
