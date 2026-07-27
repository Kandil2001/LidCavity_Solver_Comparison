SHELL := /bin/bash
ENGINE ?= auto

.PHONY: help run smoke quick medium full single plots clean

help:
	@echo "MATLAB/Octave reference solver"
	@echo "  make smoke                 smallest check"
	@echo "  make quick                 quick benchmark"
	@echo "  make medium                medium benchmark"
	@echo "  make full                  full benchmark"
	@echo "  make single                one debug case"
	@echo "  make plots                 regenerate plots from existing results"
	@echo "  make smoke ENGINE=octave   force GNU Octave instead of MATLAB"
	@echo "  make clean                 remove generated outputs"

run: smoke

smoke:
	ENGINE=$(ENGINE) ./run_matlab_or_octave.sh smoke

quick:
	ENGINE=$(ENGINE) ./run_matlab_or_octave.sh quick

medium:
	ENGINE=$(ENGINE) ./run_matlab_or_octave.sh medium

full:
	ENGINE=$(ENGINE) ./run_matlab_or_octave.sh full

single:
	ENGINE=$(ENGINE) ./run_matlab_or_octave.sh single

plots:
	ENGINE=$(ENGINE) ./run_matlab_or_octave.sh plots

clean:
	rm -rf results/data results/figures results/scaling results/logs
	mkdir -p results/data results/figures results/scaling results/logs
	touch results/.gitkeep results/data/.gitkeep results/figures/.gitkeep results/scaling/.gitkeep results/logs/.gitkeep
