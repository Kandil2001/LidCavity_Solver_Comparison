# Running on Stromboli or another Slurm cluster

## Deployment rule

Stromboli is a run-only target. Prepare and version the source on the local computer, package it, upload it with `scp`, and extract it into a new timestamped directory under `/beegfs/kandil`. Do not use Git on Stromboli and do not overwrite active result folders.

## Local preparation

```bash
python3 scripts/check_repository_consistency.py
python3 scripts/package_paper_snapshot.py   # available on the paper branch when needed
```

For the current repository, a normal source-only archive is also sufficient:

```bash
tar --exclude='.git' --exclude='bin' --exclude='__pycache__' \
    -czf lidcavity-domain-source.tar.gz .
scp lidcavity-domain-source.tar.gz \
    m2328670@stromboli.physik.uni-wuppertal.de:~/uploads/
```

## On Stromboli

```bash
mkdir -p /beegfs/kandil/paper_runs
run_dir="/beegfs/kandil/paper_runs/LidCavity_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$run_dir"
tar -xzf ~/uploads/lidcavity-domain-source.tar.gz -C "$run_dir"
cd "$run_dir"
```

Check the toolchain and clean-build before submitting arrays:

```bash
command -v gcc g++ mpicc mpicxx mpirun python3 sbatch
make rebuild-domain
```

Maintained Slurm entry points are under:

```text
hpc/stromboli/array_full_openmp_3rep.sbatch
hpc/stromboli/array_full_mpi_3rep.sbatch
hpc/stromboli/array_full_hybrid_3rep.sbatch
hpc/stromboli/run_strong_scaling_all.sbatch
```

Submit only after the small local/interactive smoke test succeeds, and always write new results to a new run directory.

## Retrieve results

From the local computer:

```bash
scp -r m2328670@stromboli.physik.uni-wuppertal.de:/beegfs/kandil/paper_runs/<RUN>/results ./results_from_stromboli
```

Commit retrieved results locally after auditing completeness and metadata.
