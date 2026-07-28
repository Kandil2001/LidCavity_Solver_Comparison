SHELL := /bin/bash
NP ?= 2
OMP_NUM_THREADS ?= 2
NUMBA_NUM_THREADS ?= 2
PYTHON ?= python3

REFERENCE_DIRS := python/serial c/serial cpp/serial c/openmp cpp/openmp
DOMAIN_OPENMP_DIRS := \
	src/c/openmp_domain_looped \
	src/c/openmp_domain_vectorized \
	src/cpp/openmp_domain_looped \
	src/cpp/openmp_domain_vectorized
DOMAIN_MPI_COMPILED_DIRS := \
	src/c/mpi_domain_looped \
	src/c/mpi_domain_vectorized \
	src/cpp/mpi_domain_looped \
	src/cpp/mpi_domain_vectorized
DOMAIN_MPI_PYTHON_DIRS := \
	src/python/mpi_domain_looped \
	src/python/mpi_domain_vectorized
DOMAIN_HYBRID_COMPILED_DIRS := \
	src/c/hybrid_mpi_openmp_looped \
	src/c/hybrid_mpi_openmp_vectorized \
	src/cpp/hybrid_mpi_openmp_looped \
	src/cpp/hybrid_mpi_openmp_vectorized
DOMAIN_HYBRID_PYTHON_DIRS := \
	src/python/hybrid_mpi_openmp_looped \
	src/python/hybrid_mpi_openmp_vectorized
DOMAIN_COMPILED_DIRS := $(DOMAIN_OPENMP_DIRS) $(DOMAIN_MPI_COMPILED_DIRS) $(DOMAIN_HYBRID_COMPILED_DIRS)
DOMAIN_ALL_DIRS := $(DOMAIN_COMPILED_DIRS) $(DOMAIN_MPI_PYTHON_DIRS) $(DOMAIN_HYBRID_PYTHON_DIRS)

.PHONY: help check rebuild-domain smoke-cpu smoke-reference smoke-domain \
	smoke-domain-openmp smoke-domain-mpi smoke-domain-hybrid selected-results \
	domain-matrix clean-reference clean-domain clean-all

help:
	@echo "Lid-driven cavity CFD/HPC benchmark"
	@echo
	@echo "Canonical commands:"
	@echo "  make check                 validate repository structure and scripts"
	@echo "  make rebuild-domain        clean-build every compiled grid-decomposition solver"
	@echo "  make smoke-cpu             run reference + OpenMP + spatial MPI + hybrid smoke tests"
	@echo "  make smoke-reference       run the earlier serial/OpenMP pressure-correction track"
	@echo "  make smoke-domain-openmp   run C/C++ domain OpenMP variants"
	@echo "  make smoke-domain-mpi      run C/C++/Python spatial MPI variants"
	@echo "  make smoke-domain-hybrid   run C/C++/Python hybrid variants"
	@echo "  make selected-results      regenerate compact README results without running CFD"
	@echo "  make domain-matrix         run the configurable domain benchmark script"
	@echo "  make clean-all             remove generated build and smoke outputs"
	@echo
	@echo "Variables: NP=$(NP), OMP_NUM_THREADS=$(OMP_NUM_THREADS), NUMBA_NUM_THREADS=$(NUMBA_NUM_THREADS)"

check:
	$(PYTHON) scripts/check_repository_consistency.py

rebuild-domain:
	@command -v gcc >/dev/null || { echo "gcc is required" >&2; exit 1; }
	@command -v g++ >/dev/null || { echo "g++ is required" >&2; exit 1; }
	@command -v mpicc >/dev/null || { echo "mpicc is required" >&2; exit 1; }
	@command -v mpicxx >/dev/null || { echo "mpicxx is required" >&2; exit 1; }
	@set -e; for d in $(DOMAIN_COMPILED_DIRS); do \
		echo "==> clean-build $$d"; \
		$(MAKE) -C "$$d" clean; \
		$(MAKE) -C "$$d" build; \
	done

smoke-cpu: smoke-reference smoke-domain

smoke-reference:
	NP=$(NP) OMP_NUM_THREADS=$(OMP_NUM_THREADS) bash scripts/run_smoke_cpu.sh reference

smoke-domain: smoke-domain-openmp smoke-domain-mpi smoke-domain-hybrid

smoke-domain-openmp:
	@set -e; for d in $(DOMAIN_OPENMP_DIRS); do \
		echo "==> smoke $$d"; \
		$(MAKE) -C "$$d" smoke OMP_NUM_THREADS=$(OMP_NUM_THREADS); \
	done

smoke-domain-mpi:
	@command -v mpirun >/dev/null || { echo "mpirun is required" >&2; exit 1; }
	@set -e; for d in $(DOMAIN_MPI_COMPILED_DIRS); do \
		echo "==> smoke $$d"; \
		$(MAKE) -C "$$d" smoke NP=$(NP); \
	done
	@set -e; for d in $(DOMAIN_MPI_PYTHON_DIRS); do \
		echo "==> smoke $$d"; \
		$(MAKE) -C "$$d" smoke NP=$(NP) PYTHON=$(PYTHON); \
	done

smoke-domain-hybrid:
	@command -v mpirun >/dev/null || { echo "mpirun is required" >&2; exit 1; }
	@set -e; for d in $(DOMAIN_HYBRID_COMPILED_DIRS); do \
		echo "==> smoke $$d"; \
		$(MAKE) -C "$$d" smoke NP=$(NP) OMP_NUM_THREADS=$(OMP_NUM_THREADS); \
	done
	@set -e; for d in $(DOMAIN_HYBRID_PYTHON_DIRS); do \
		echo "==> smoke $$d"; \
		$(MAKE) -C "$$d" smoke NP=$(NP) NUMBA_NUM_THREADS=$(NUMBA_NUM_THREADS) PYTHON=$(PYTHON); \
	done

selected-results:
	$(PYTHON) scripts/generate_selected_results.py

domain-matrix:
	NP=$(NP) OMP_NUM_THREADS=$(OMP_NUM_THREADS) NUMBA_NUM_THREADS=$(NUMBA_NUM_THREADS) \
		bash scripts/run_domain_solver_benchmark.sh

clean-reference:
	@for d in matlab $(REFERENCE_DIRS) cuda comparison; do \
		if [[ -f "$$d/Makefile" ]]; then echo "==> clean $$d"; $(MAKE) -C "$$d" clean >/dev/null || true; fi; \
	done

clean-domain:
	@for d in $(DOMAIN_ALL_DIRS); do \
		echo "==> clean $$d"; $(MAKE) -C "$$d" clean >/dev/null || true; \
	done

clean-all: clean-reference clean-domain
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +
