# Running on a university or HPC machine

Start with a smoke run. It checks that the folders compile and that the Python scripts can start.

```bash
make smoke-cpu
```

For longer runs, use `nohup` or a batch system if the machine supports it.

```bash
nohup make quick-cpu > quick_cpu.log 2>&1 &
```

Check the log while it is running:

```bash
tail -f quick_cpu.log
```

Show the last 300 lines:

```bash
tail -n 300 quick_cpu.log
```

Check whether the process is still active:

```bash
ps -f -u "$USER" | grep -E "lid_cavity|matlab|octave|python|make" | grep -v grep
```



## Full Stromboli workflow

Use this from the repository root when you want one command that checks the available tools and runs what can run on the current node:

```bash
bash scripts/run_stromboli_all.sh smoke
```

For a longer run that survives a dropped SSH connection:

```bash
nohup bash scripts/run_stromboli_all.sh quick > stromboli_quick.log 2>&1 &
tail -f stromboli_quick.log
```

The script attempts to make common cluster tools available, including the OpenMPI path observed on Stromboli-like machines:

```text
/cluster/mpi/openmpi/4.1.8/bin
```

It then runs Octave, serial CPU solvers, OpenMP solvers, MPI solvers, and CUDA when the required tools are available. Missing optional tools are reported and skipped.

To skip CUDA intentionally on a CPU-only node:

```bash
RUN_CUDA=0 bash scripts/run_stromboli_all.sh quick
```

## GNU Octave on Stromboli

If MATLAB is not available on Stromboli, use GNU Octave for the `matlab/` reference solver.

First check whether Octave is available:

```bash
module avail octave
module load octave
which octave
octave --version
```

Then run the reference solver directly:

```bash
cd matlab
make smoke ENGINE=octave
make quick ENGINE=octave
```

Or use the helper from the repository root:

```bash
bash scripts/run_stromboli_octave.sh smoke
bash scripts/run_stromboli_octave.sh quick
```

For a run that survives a dropped SSH connection:

```bash
nohup bash scripts/run_stromboli_octave.sh quick > octave_quick.log 2>&1 &
tail -f octave_quick.log
```

Octave skips plot generation by default on the cluster and writes CSV/`.mat` outputs under `matlab/results/data/`. To force Octave plots, set:

```bash
OCTAVE_MAKE_FIGURES=1 bash scripts/run_stromboli_octave.sh quick
```

## MPI

MPI runs need `mpirun` and usually `mpicc` for the C/C++ drivers.

```bash
which mpirun
which mpicc
```

Then run for example:

```bash
cd c/mpi
make quick NP=4
```

## CUDA

CUDA runs need an NVIDIA GPU, `nvcc`, and access to the GPU from the current node.

```bash
cd cuda
make check-cuda
make smoke
make scaling
```

From the repository root, you can also run:

```bash
make smoke-cuda
make scaling-cuda
```

If `nvidia-smi` fails, the current node probably has no accessible NVIDIA GPU. In that case, skip `cuda/` on this node or move the run to a GPU node. The Stromboli all-in-one script automatically skips CUDA when the GPU tools are missing.
