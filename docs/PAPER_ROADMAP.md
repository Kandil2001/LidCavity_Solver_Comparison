# Paper development roadmap

## Goal

Build a simple, reproducible software paper comparing the same lid-driven-cavity pressure-correction algorithm across Python, C, C++, and optional Rust, with OpenFOAM as an external reference.

The contribution is the transparent cross-language implementation, numerical-equivalence testing, and reproducible performance study. The cavity algorithm itself is not claimed as new.

## Scope decision

### Main benchmark

- Python/NumPy serial
- C serial
- C++ serial
- Rust serial if available on the target system
- C/OpenMP
- C++/OpenMP
- Rust/Rayon if Rust is available

### Separate analyses

- Existing MPI implementations: parameter-sweep throughput
- OpenFOAM: external engineering reference

### Outside the first paper

- MATLAB and Octave
- CUDA
- True spatial-domain MPI decomposition
- Additional languages

The MATLAB and Octave code remains in the repository as previous work, but is not required for the paper because it cannot be executed consistently on Stromboli.

## Stromboli operating rule

Stromboli is a run-only machine for this project. Do not clone, initialize, fetch,
pull, checkout, switch branches, create worktrees, or commit with Git there.

Prepare a source-only archive locally, transfer it with `scp`, extract each
snapshot into a separate timestamped directory, and return results with `scp` or
`rsync`. See [`STROMBOLI_NO_GIT.md`](STROMBOLI_NO_GIT.md).

## Phase 0 — Preserve current work

- [ ] Allow already-running jobs to finish.
- [ ] Copy their complete outputs into a clearly labelled `pilot_v0` dataset.
- [ ] Preserve logs, Slurm job IDs, node names, and failure information.
- [ ] Do not use pilot timings as the final paper ranking.

## Phase 1 — Confirm available software

Package the branch locally with:

```bash
python3 scripts/package_paper_snapshot.py
```

Copy and extract the snapshot on Stromboli without Git, then run:

```bash
bash scripts/check_paper_toolchain.sh \
  --output comparison/results/toolchain/stromboli.txt
```

Decision rules:

- Rust joins the main paper only when both `rustc` and `cargo` are available or a documented user-space installation is used for every final run.
- OpenFOAM joins only when a reproducible version and environment can be loaded.
- Python, GCC, G++, Make, OpenMPI, and Slurm remain the required baseline.

## Phase 2 — Freeze the numerical specification

- [x] Add the draft paper case matrix.
- [x] Use odd grids: `33`, `65`, `129`, `257`.
- [x] Use central convection and RBSOR for the primary comparison.
- [x] Separate execution, convergence, pressure, and validation status.
- [ ] Confirm final tolerances using a sensitivity study.
- [ ] Confirm one common SOR relaxation strategy.
- [ ] Freeze the specification before running final timings.

See:

- `benchmark/paper_cases.yaml`
- `benchmark/NUMERICAL_SPECIFICATION.md`

## Phase 3 — Repair the C++ serial reference

First target:

```text
N = 65
Re = 100
Scheme = central
Pressure solver = RBSOR
```

Required changes:

- [ ] Rename velocity-change quantities so they are not called momentum residuals.
- [ ] Tighten and consistently report the pressure Poisson residual.
- [ ] Reuse a previous pressure-correction estimate where appropriate.
- [x] Require pressure convergence in the paper-protocol outer convergence decision.
- [x] Add explicit booleans for outer and pressure convergence.
- [ ] Export solver time separately from file-output time.
- [ ] Export complete run metadata.
- [ ] Demonstrate stable, repeatable convergence for the first target case.

Do not port unfinished numerical changes to every language. Fix and validate the C++ reference first.

## Phase 4 — Verification and validation

- [ ] Add analytical derivative tests.
- [ ] Add Laplacian and Poisson tests.
- [ ] Add divergence-free-field and vorticity tests.
- [ ] Add boundary-condition tests.
- [ ] Sample exact cavity centerlines.
- [ ] Report L1, L2, and Linf Ghia errors.
- [ ] Report primary-vortex location.
- [ ] Show systematic grid trends.

## Phase 5 — Synchronize existing languages

Port the frozen C++ behaviour to:

- [ ] C serial
- [ ] Python/NumPy serial
- [ ] C/OpenMP
- [ ] C++/OpenMP

Acceptance condition:

- Matched converged fields agree within documented floating-point tolerances.
- Parallel and serial variants produce equivalent physical results.

## Phase 6 — Rust decision and implementation

After running the toolchain check:

- [ ] Record whether Rust is available on Stromboli.
- [ ] If available, add `rust_serial` using a flat `Vec<f64>` layout.
- [ ] Validate Rust against C++ field outputs.
- [ ] Add `rust_rayon` only after serial equivalence is established.
- [ ] If unavailable, remove Rust from the final headline rather than running it on incomparable hardware.

## Phase 7 — OpenFOAM reference

- [ ] Confirm the installed OpenFOAM distribution and version.
- [ ] Create equivalent Re 100, 400, and 1000 cases.
- [ ] Match geometry, lid speed, viscosity, and approximate grids.
- [ ] Export exact centerline profiles and vortex information.
- [ ] Record end-to-end and solver runtimes.
- [ ] Present OpenFOAM separately from the identical-algorithm comparison.

## Phase 8 — Final benchmark runs

- [ ] Use one warm-up run.
- [ ] Use at least five measured repetitions.
- [ ] Disable field output inside timed sections.
- [ ] Preserve every raw timing.
- [ ] Record compiler, interpreter, node, CPU, snapshot identifier, thread, and rank metadata.
- [ ] Exclude non-converged runs from performance ranking.
- [ ] Report median and interquartile range.

## Phase 9 — Paper and release

- [ ] Generate every final table and figure from scripts.
- [ ] Add the manuscript source under `paper/`.
- [ ] Create a tagged `v1.0.0` release.
- [ ] Update `CITATION.cff` with the release version and date.
- [ ] Archive the software release and final data.

## Immediate next task

The next numerical change should remain limited to the C++ serial solver and its output schema. The immediate success condition is one fully converged `N=65`, `Re=100`, central/RBSOR result with separate pressure and outer convergence reporting.
