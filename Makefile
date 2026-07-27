SHELL := /bin/bash
MODE ?= quick
NP ?= 4
OMP_NUM_THREADS ?= 4
PYTHON ?= python3

.PHONY: help smoke-cpu quick-cpu smoke-cuda quick-cuda smoke-stromboli quick-stromboli compare-serial report-serial aggregate-data grid-convergence validation-plots scaling-openmp scaling-mpi scaling-cuda scaling-all clean-all

help:
	@echo "Lid-driven cavity solver comparison"
	@echo ""
	@echo "Common commands from the repo root:"
	@echo "  make smoke-cpu                    run smallest CPU checks, skipping missing tools"
	@echo "  make quick-cpu                    run quick CPU benchmarks, skipping missing tools"
	@echo "  make compare-serial MODE=quick    compare serial MATLAB/C++/C/Python outputs"
	@echo "  make report-serial MODE=quick     create benchmark tables and plots"
	@echo "  make aggregate-data MODE=full     aggregate CSV comparisons without images"
	@echo "  make grid-convergence             run C++ grid convergence study"
	@echo "  make validation-plots             plot U/V centerlines against Ghia data"
	@echo "  make scaling-openmp               run OpenMP strong-scaling plots"
	@echo "  make scaling-mpi                  run MPI case-level scaling plots"
	@echo "  make scaling-cuda                 run CUDA block-size performance plots"
	@echo "  make scaling-all                  run OpenMP + MPI + CUDA scaling plots"
	@echo "  make smoke-stromboli              run Stromboli smoke workflow, including CUDA if available"
	@echo "  make quick-stromboli              run Stromboli quick workflow, including CUDA if available"
	@echo "  make clean-all                    remove generated build/results folders"
	@echo ""
	@echo "Variables: MODE=smoke|quick|medium|full, NP=4, OMP_NUM_THREADS=4, PYTHON=python3, RUN_CUDA=1"

smoke-cpu:
	bash scripts/run_smoke_cpu.sh

quick-cpu:
	bash scripts/run_quick_cpu.sh

smoke-cuda:
	$(MAKE) -C cuda smoke

quick-cuda:
	$(MAKE) -C cuda quick

smoke-stromboli:
	bash scripts/run_stromboli_all.sh smoke

quick-stromboli:
	bash scripts/run_stromboli_all.sh quick

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

aggregate-data:
	$(PYTHON) scripts/aggregate_full_study_data.py --mode $(MODE)

grid-convergence:
	$(PYTHON) scripts/run_grid_convergence.py --solver cpp --N-list 32,64,128 --Re 100 --scheme upwind --pressure RBGS

validation-plots:
	$(PYTHON) scripts/plot_validation_centerlines.py --Re 100

scaling-openmp:
	$(PYTHON) scripts/run_parallel_scaling.py --targets c_openmp,cpp_openmp --threads 1,2,4,8 --N 64 --Re 100 --scheme upwind --pressure RBGS

scaling-mpi:
	$(PYTHON) scripts/run_parallel_scaling.py --targets c_mpi,cpp_mpi,python_mpi --ranks 1,2,4 --mode $(MODE)

scaling-cuda:
	$(PYTHON) scripts/run_cuda_scaling.py --block-sizes 64,128,256 --N 64 --Re 100 --scheme upwind --pressure JACOBI

scaling-all:
	$(PYTHON) scripts/run_parallel_scaling.py --targets c_openmp,cpp_openmp,c_mpi,cpp_mpi,python_mpi --threads 1,2,4,8 --ranks 1,2,4 --mode $(MODE) --N 64 --Re 100 --scheme upwind --pressure RBGS
	$(PYTHON) scripts/run_cuda_scaling.py --block-sizes 64,128,256 --N 64 --Re 100 --scheme upwind --pressure JACOBI --skip-if-missing

clean-all:
	@for d in matlab python/serial python/mpi c/serial c/openmp c/mpi cpp/serial cpp/openmp cpp/mpi cuda comparison; do \
		if [ -f "$$d/Makefile" ]; then echo "clean $$d"; $(MAKE) -C "$$d" clean >/dev/null || true; fi; \
	done
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +
