# Stromboli ready run

This zip is prepared to avoid the old problems:

- uses conda Python 3.10 instead of system Python 3.6
- uses conda Octave if available/installed
- fixes the C++ `std::filesystem` linker problem on GCC 8
- fixes the broken Octave/MATLAB `fprintf` syntax
- runs serial/OpenMP/Python/Octave cases as Slurm arrays: each physical case is its own Slurm task
- runs C/C++/Python MPI as separate 8-rank MPI jobs

## Run

```bash
cd ~
unzip -q LidCavity_Solver_Comparison_stromboli_ready_divided.zip
cd LidCavity_Solver_Comparison
```

If `~/software/miniforge3` / `lid_env` is missing:

```bash
bash 00_setup_lid_env.sh
```

Prepare project:

```bash
bash 01_prepare_stromboli.sh
```

Test one small case:

```bash
bash 02_test_one_case.sh
squeue -u $USER
```

After the test finishes, check the result:

```bash
ls -lh comparison/results/split/c_serial_case_001.csv
cat logs/test_one_case_*.err
```

Submit everything divided:

```bash
bash 03_submit_all.sh
```

Check status:

```bash
bash jobs/status.sh
```

After `squeue -u $USER` is empty, merge:

```bash
bash 04_merge_after_finish.sh
```

Expected split CSV count: 288 from arrays, plus MPI raw files.
