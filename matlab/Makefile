SHELL := /bin/bash
MATLAB ?= matlab
MATLAB_ENTRY := addpath('src/app')

.PHONY: help run smoke quick medium full single plots clean

help:
	@echo "MATLAB reference solver"
	@echo "  make smoke    smallest check"
	@echo "  make quick    quick benchmark"
	@echo "  make medium   medium benchmark"
	@echo "  make full     full benchmark"
	@echo "  make single   one debug case"
	@echo "  make plots    regenerate MATLAB plots from existing results"
	@echo "  make clean    remove generated outputs"

run: smoke

smoke:
	$(MATLAB) -batch "$(MATLAB_ENTRY); run_smoke"

quick:
	$(MATLAB) -batch "$(MATLAB_ENTRY); run_quick"

medium:
	$(MATLAB) -batch "$(MATLAB_ENTRY); run_medium"

full:
	$(MATLAB) -batch "$(MATLAB_ENTRY); run_full"

single:
	$(MATLAB) -batch "$(MATLAB_ENTRY); addpath('src/studies'); run_single_case"

plots:
	$(MATLAB) -batch "$(MATLAB_ENTRY); generate_all_plots_from_results"

clean:
	rm -rf results/data results/figures results/scaling results/logs
	mkdir -p results/data results/figures results/scaling results/logs
	touch results/.gitkeep results/data/.gitkeep results/figures/.gitkeep results/scaling/.gitkeep results/logs/.gitkeep
