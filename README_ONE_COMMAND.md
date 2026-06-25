# One-command Stromboli run

From an empty Stromboli home folder, upload this zip, then run:

```bash
cd ~
rm -rf LidCavity_Solver_Comparison
unzip -q LidCavity_Solver_Comparison_ONE_RUN_STROMBOLI.zip
cd LidCavity_Solver_Comparison
bash RUN_EVERYTHING_ON_STROMBOLI.sh
```

This one script:

- installs/recreates `~/software/miniforge3` and `lid_env` if missing
- uses Python 3.10, Octave, and mpi4py from conda
- prepares the repo and GCC 8 C++ fix
- runs serial/OpenMP/Python/Octave as divided Slurm arrays
- runs C/C++/Python MPI with 8 ranks
- schedules a final merge/report job automatically

Check status later:

```bash
cd ~/LidCavity_Solver_Comparison
bash jobs/status.sh
squeue -u $USER
```

When all jobs finish, the final report is in:

```bash
ls -t logs/final_merge_report_*.out | head -1
cat $(ls -t logs/final_merge_report_*.out | head -1)
```
