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
ps -f -u "$USER" | grep -E "lid_cavity|matlab|python|make" | grep -v grep
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

CUDA runs need an NVIDIA GPU and `nvcc`.

```bash
nvidia-smi
nvcc --version
```

If the machine has no NVIDIA GPU, skip the `cuda/` folder.
