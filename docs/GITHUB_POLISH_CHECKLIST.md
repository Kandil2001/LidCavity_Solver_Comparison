# GitHub Polish Checklist

Use this checklist before sharing the repository on LinkedIn, in a CV, or with a supervisor.

## Before pushing

- Run `make smoke-cpu` from the root.
- Check that the root `README.md` opens correctly on GitHub.
- Check that every solver folder has a short `README.md`.
- Remove local build folders such as `bin/`.
- Remove temporary logs unless they are useful final evidence.
- Keep generated results out of Git unless they are selected final figures or summary tables.

## Good files to keep

- Source code
- Makefiles
- README files
- Documentation notes
- Final selected plots
- Final selected benchmark tables

## Files usually not worth committing

- Full raw field CSV files from every run
- Temporary logs
- Cache folders
- Local virtual environments
- Build binaries

## After the full benchmark run

Add a small results section to the root README with:

- one runtime table
- one validation table
- one residual plot
- one velocity/streamline plot
- a short explanation of the main trend

Keep it simple. A clear repo is better than a crowded repo.
