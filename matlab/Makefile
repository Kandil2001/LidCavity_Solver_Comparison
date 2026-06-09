SHELL := /bin/bash

.PHONY: run smoke quick medium full plots clean

run:
	matlab -batch "run_smoke"

smoke:
	matlab -batch "run_smoke"

quick:
	matlab -batch "run_quick"

medium:
	matlab -batch "run_medium"

full:
	matlab -batch "run_mode('full')"

plots:
	matlab -batch "generate_all_plots_from_results"

clean:
	rm -rf results/data results/figures results/scaling results/logs
	mkdir -p results/data results/figures results/scaling results/logs
	touch results/.gitkeep results/data/.gitkeep results/figures/.gitkeep results/scaling/.gitkeep results/logs/.gitkeep
