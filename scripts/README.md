# Root Helper Scripts

This folder contains small shell/Python scripts used by the root `Makefile`.

| Script | Purpose |
|---|---|
| `run_smoke_cpu.sh` | Run the smallest CPU checks and skip missing optional tools |
| `run_quick_cpu.sh` | Run a larger quick CPU check and skip missing optional tools |
| `run_stromboli_octave.sh` | Force the MATLAB-compatible reference solver to run with GNU Octave on Stromboli/cluster machines |
| `run_stromboli_all.sh` | Run the Stromboli workflow and include CUDA automatically when GPU tools are available |
| `run_grid_convergence.py` | Run selected serial solver across progressively finer grids and estimate observed order |
| `plot_validation_centerlines.py` | Plot U/V centerline profiles against Ghia benchmark data |
| `run_parallel_scaling.py` | Run OpenMP/MPI scaling checks and generate CSV/PNG outputs |
| `run_cuda_scaling.py` | Run a CUDA block-size performance sweep and generate CSV/PNG outputs |

The scripts are written for Linux-style shells. On Windows, use WSL, Git Bash, or run the individual solver folders manually.

## Example full Stromboli run

```bash
bash scripts/run_stromboli_all.sh smoke
nohup bash scripts/run_stromboli_all.sh quick > stromboli_quick.log 2>&1 &
tail -f stromboli_quick.log
```

Use `RUN_CUDA=0` when you are on a CPU-only node and want to skip CUDA explicitly.

## Example Octave-only run on Stromboli

```bash
bash scripts/run_stromboli_octave.sh smoke
nohup bash scripts/run_stromboli_octave.sh quick > octave_quick.log 2>&1 &
tail -f octave_quick.log
```

## Example automated studies

```bash
make grid-convergence
make validation-plots
make scaling-openmp
make scaling-mpi MODE=quick
make scaling-cuda
```

Notes:

- OpenMP scaling is a fixed-case strong-scaling check.
- MPI scaling is case-level parameter-study scaling, not domain-decomposition scaling.
- Grid convergence is estimated against Ghia centerline benchmark data.
- CUDA scaling is a GPU block-size sweep, not a domain-decomposition study.

## Full data-first Stromboli run

Use this when you want the full no-CUDA study with maximum Slurm-level
parallelism, but no final image plots yet:

```bash
bash scripts/submit_stromboli_full_data_first_no_cuda.sh
```

The script creates separate Slurm jobs for serial, OpenMP, and MPI studies.
Postprocessing waits for those jobs and then runs:

```bash
python3 scripts/aggregate_full_study_data.py --mode full
```

The postprocessor creates CSV and Markdown comparison files under:

```text
comparison/results/data_first/
```

No PNG/PDF/SVG plots are created by the data-first workflow.
