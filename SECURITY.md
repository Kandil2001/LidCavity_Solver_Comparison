# Security Policy

This repository is an educational CFD/HPC benchmark project. It is not a production service and does not process sensitive user data by design.

## Supported versions

Security updates are applied to the default branch:

| Branch | Supported |
|---|---|
| `main` | yes |
| old feature branches | no |

## Reporting a vulnerability

If you find a security issue in this repository, please do **not** open a public issue with exploit details.

Instead, contact the maintainer privately:

- Email: a.akandil@outlook.com

Please include:

- a short description of the issue
- affected file or workflow
- steps to reproduce, if safe to share
- possible impact

## Scope

Relevant security concerns include:

- unsafe shell commands in scripts
- accidental credential exposure
- unsafe download or setup scripts
- dependency issues in reproducible environments
- malicious or unexpected behaviour in helper scripts

Out of scope:

- numerical accuracy disagreements
- performance differences between implementations
- expected crashes caused by unsupported compilers, missing MPI, missing CUDA, or incompatible MATLAB/Octave installations

## Dependency note

The repository uses Python, compiler toolchains, MPI, optional MATLAB/Octave, and optional CUDA. Users should install dependencies from trusted sources and review setup scripts before running them on shared HPC systems.
