SHELL := /bin/bash

.PHONY: run smoke quick medium plots clean

run:
	matlab -batch "run_smoke"

smoke:
	matlab -batch "run_smoke"

quick:
	matlab -batch "run_quick"

medium:
	matlab -batch "run_medium"

plots:
	matlab -batch "generate_all_plots_from_results"

clean:
	rm -rf results
	mkdir -p results
	touch results/.gitkeep
