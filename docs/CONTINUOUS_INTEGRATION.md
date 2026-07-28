# Continuous integration

The workflow in `.github/workflows/cpu-smoke.yml` verifies repository integrity and the complete small CPU implementation matrix.

It performs:

1. installation of OpenMPI and pinned Python dependencies;
2. repository consistency checks;
3. a clean rebuild of every compiled domain implementation;
4. smoke execution of the pressure-correction serial/OpenMP reference track;
5. smoke execution of domain OpenMP, spatial MPI, and hybrid implementations;
6. readable summary-CSV verification for every tested implementation;
7. regeneration of `results/selected/` and a Git diff check.

A green workflow proves that these small configured cases build, run, and generate parseable outputs in the pinned CI environment. It does not prove production-case convergence, physical validation, scalability on Stromboli, or CUDA correctness.
