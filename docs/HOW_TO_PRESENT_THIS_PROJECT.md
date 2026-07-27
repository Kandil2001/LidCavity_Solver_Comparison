# How to present this project

Use wording that is technical, clear, and honest.

## Good short description

> I built a lid-driven cavity benchmark to compare the same CFD setup across MATLAB, Python, C, C++, OpenMP, MPI case-parallel runs, and a CUDA prototype. The project focuses on solver structure, validation against Ghia data, runtime comparison, and reproducible CSV/plot outputs.

## Good CV bullet

> Developed a multi-language lid-driven cavity benchmark using MATLAB/Octave, Python, C, C++, OpenMP, MPI case-level parallelism, and CUDA; added automated Ghia validation plots, grid-convergence tables, and scaling plots using a consistent SIMPLE-style setup.

## Good interview explanation

> I wanted to show that I can take one CFD problem and implement it in several environments. MATLAB is the reference workflow, Python is readable and post-processing-friendly, C and C++ are compiled baselines, OpenMP tests shared-memory parallelism, MPI distributes independent cases, and CUDA is a GPU prototype. I also kept the comparison honest by matching cases through mesh, Reynolds number, scheme, and pressure solver instead of comparing files by order.

## Avoid saying this

Do not say that the project is a production CFD solver.

Do not say that MPI is domain decomposition yet.

Do not say that every MPI/OpenMP solver has true vectorized and looped implementations. Python and MATLAB/Octave have clearer loop/vectorized study paths. Python MPI can distribute those Python cases. C/C++ OpenMP and C/C++ MPI are single baseline implementations.

Do not claim CUDA is automatically faster before running it on a suitable GPU and comparing the same cases carefully.
