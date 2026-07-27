CXX ?= g++
CXXFLAGS ?= -std=c++17 -O2  -Wall -Wextra -pedantic -g0 -fopenmp
NO_FIELDS ?= 0
NO_FIELDS_FLAG := $(if $(filter 1 true yes,$(NO_FIELDS)),--no-fields,)
BIN = bin/lid_cavity_openmp
OMP_NUM_THREADS ?= 4

.PHONY: build run smoke quick medium full scaling plot clean

build:
	mkdir -p bin
	$(CXX) $(CXXFLAGS) src/lid_cavity.cpp -o $(BIN) -lstdc++fs

run: build
	OMP_NUM_THREADS=$(OMP_NUM_THREADS) $(BIN) --single --N $(or $(N),64) --Re $(or $(RE),100) --scheme $(or $(SCHEME),central) --pressure $(or $(PRESSURE),RBGS) $(NO_FIELDS_FLAG)

smoke: build
	OMP_NUM_THREADS=$(OMP_NUM_THREADS) $(BIN) --mode smoke $(NO_FIELDS_FLAG)

quick: build
	OMP_NUM_THREADS=$(OMP_NUM_THREADS) $(BIN) --mode quick $(NO_FIELDS_FLAG)

medium: build
	OMP_NUM_THREADS=$(OMP_NUM_THREADS) $(BIN) --mode medium $(NO_FIELDS_FLAG)

full: build
	OMP_NUM_THREADS=$(OMP_NUM_THREADS) $(BIN) --mode full $(NO_FIELDS_FLAG)

scaling:
	../../scripts/run_parallel_scaling.py --targets cpp_openmp --threads $(or $(THREADS),1,2,4,8) --N $(or $(N),64) --Re $(or $(RE),100) --scheme $(or $(SCHEME),upwind) --pressure $(or $(PRESSURE),RBGS)

plot:
	python3 postprocess/plot_results.py --all-cases --summaries all

clean:
	rm -rf bin results/data results/figures results/scaling results/logs results/mpi_raw __pycache__ src/__pycache__
	mkdir -p results/data results/figures results/scaling results/logs
	touch results/.gitkeep results/data/.gitkeep results/figures/.gitkeep results/scaling/.gitkeep results/logs/.gitkeep
