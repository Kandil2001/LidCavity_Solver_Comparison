SHELL := /bin/bash
MODE ?= quick
NP ?= 4
OMP_NUM_THREADS ?= 4
PYTHON ?= python3

.PHONY: help smoke-cpu quick-cpu compare-serial report-serial scaling-openmp clean-all

help:
	@echo "Lid-driven cavity solver comparison"
	@echo ""
	@echo "Common commands from the repo root:"
	@echo "  make smoke-cpu                  run smallest CPU checks, skipping missing tools"
	@echo "  make quick-cpu                  run quick CPU benchmarks, skipping missing tools"
	@echo "  make compare-serial MODE=quick  compare serial MATLAB/C++/C/Python outputs"
	@echo "  make report-serial MODE=quick   create benchmark tables and plots"
	@echo "  make scaling-openmp             run small OpenMP scaling checks"
	@echo "  make clean-all                  remove generated build/results folders"
	@echo ""
	@echo "Variables: MODE=smoke|quick|medium|full, NP=4, OMP_NUM_THREADS=4, PYTHON=python3"

smoke-cpu:
	bash scripts/run_smoke_cpu.sh

quick-cpu:
	bash scripts/run_quick_cpu.sh

compare-serial:
	$(PYTHON) comparison/compare_outputs.py \
		--reference-data matlab/results/data \
		--reference-summary study_summary_$(MODE)_matlab.csv \
		--reference-label MATLAB \
		--cpp-data cpp/serial/results/data \
		--cpp-summary study_summary_$(MODE).csv \
		--c-data c/serial/results/data \
		--c-summary study_summary_$(MODE).csv \
		--python-data python/serial/results/data \
		--python-summary study_summary_$(MODE).csv \
		--out comparison/results

report-serial:
	$(PYTHON) comparison/benchmark_report.py \
		--matlab-summary matlab/results/data/study_summary_$(MODE)_matlab.csv \
		--cpp-summary cpp/serial/results/data/study_summary_$(MODE).csv \
		--c-summary c/serial/results/data/study_summary_$(MODE).csv \
		--python-summary python/serial/results/data/study_summary_$(MODE).csv \
		--comparison comparison/results/comparison_summary.csv \
		--out comparison/results

scaling-openmp:
	$(MAKE) -C c/openmp scaling OMP_NUM_THREADS=$(OMP_NUM_THREADS)
	$(MAKE) -C cpp/openmp scaling OMP_NUM_THREADS=$(OMP_NUM_THREADS)
	$(PYTHON) comparison/postprocess/plot_parallel_scaling.py

clean-all:
	@for d in matlab python/serial python/mpi c/serial c/openmp c/mpi cpp/serial cpp/openmp cpp/mpi cuda comparison; do \
		if [ -f "$$d/Makefile" ]; then echo "clean $$d"; $(MAKE) -C "$$d" clean >/dev/null || true; fi; \
	done
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +
