# MATLAB solver

This is the reference workflow for the project. I use it to keep the numerical setup clear before comparing with the compiled versions.

It contains both MATLAB-style looped code and vectorized parts, plus validation and plotting routines.

## Run

```bash
make smoke     # smallest check
make quick     # small benchmark
make medium    # larger benchmark
make plots     # regenerate plots from saved results
```

MATLAB writes results to:

```text
results/data/
results/figures/
```

The main summary file for a quick run is:

```text
results/data/study_summary_quick_matlab.csv
```
