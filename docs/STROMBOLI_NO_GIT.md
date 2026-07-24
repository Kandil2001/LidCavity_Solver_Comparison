# Stromboli deployment without Git

Stromboli is treated as a run-only machine for the paper benchmark.

Do not run any of the following commands on Stromboli:

```text
git clone
git init
git fetch
git pull
git checkout
git switch
git worktree
```

The source snapshot is prepared on another machine, copied with `scp`, and
extracted into a separate run directory. Existing Stromboli result directories
and running Slurm jobs are not touched.

## 1. Prepare the source snapshot locally

On the local checkout of the paper branch:

```bash
python3 scripts/package_paper_snapshot.py
```

The script creates two files under `dist/`:

```text
lidcavity-paper-snapshot-<UTC timestamp>.tar.gz
lidcavity-paper-snapshot-<UTC timestamp>.tar.gz.sha256
```

The archive excludes:

- `.git` and other editor metadata
- existing result and figure trees
- binaries and object files
- Python virtual environments and caches
- old archives

The archive contains a `SNAPSHOT_MANIFEST.json` file with the creation time and,
when available locally, the source commit identifier.

## 2. Copy the snapshot to Stromboli

Create the upload directory first:

```bash
ssh m2328670@stromboli.physik.uni-wuppertal.de "mkdir -p ~/uploads"
```

Then copy the archive, checksum, and extraction helper from PowerShell, WSL,
Linux, or macOS:

```bash
scp dist/lidcavity-paper-snapshot-*.tar.gz \
  m2328670@stromboli.physik.uni-wuppertal.de:~/uploads/

scp dist/lidcavity-paper-snapshot-*.tar.gz.sha256 \
  m2328670@stromboli.physik.uni-wuppertal.de:~/uploads/

scp scripts/unpack_paper_snapshot.sh \
  m2328670@stromboli.physik.uni-wuppertal.de:~/uploads/
```

This uses SSH and SCP only. It does not use Git on Stromboli.

## 3. Extract into a separate run directory

On Stromboli:

```bash
mkdir -p /beegfs/kandil/paper_runs

bash ~/uploads/unpack_paper_snapshot.sh \
  ~/uploads/lidcavity-paper-snapshot-<timestamp>.tar.gz \
  /beegfs/kandil/paper_runs
```

The helper verifies the SHA-256 checksum when the sidecar file is present and
extracts the source into a new timestamped directory.

Direct extraction is also possible:

```bash
run_dir=/beegfs/kandil/paper_runs/LidCavity_Paper_$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$run_dir"
tar -xzf ~/uploads/lidcavity-paper-snapshot-<timestamp>.tar.gz \
  -C "$run_dir" --strip-components=1
cd "$run_dir"
```

Every upload should receive its own timestamped directory. Do not overwrite the
folder used by currently running jobs.

## 4. Check the available tools

From the extracted directory:

```bash
bash scripts/check_paper_toolchain.sh \
  --output comparison/results/toolchain/stromboli.txt

cat comparison/results/toolchain/stromboli.txt
```

This determines whether Rust and OpenFOAM are available without installing or
changing anything.

Rust is included in the paper only when both `rustc` and `cargo` are available.
OpenFOAM is included only when its commands and environment are accessible.
Python, C, and C++ remain the guaranteed core comparison.

## 5. Run through Slurm

Do not launch full paper cases on a login node. First prepare a one-case Slurm
job for:

```text
N = 65
Re = 100
scheme = central
pressure solver = RBSOR
implementation = C++ serial
```

The run must write into its own directory under:

```text
comparison/results/paper_v1/raw/
```

The existing pilot jobs and result folders are left unchanged.

## 6. Return results without Git

Copy the completed result folder back using `scp` or `rsync`:

```bash
scp -r \
  m2328670@stromboli.physik.uni-wuppertal.de:/beegfs/kandil/paper_runs/<run>/comparison/results/paper_v1/raw \
  ./stromboli_results/
```

Results are reviewed and committed from the local development environment, not
from Stromboli.
