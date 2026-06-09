CXX ?= g++
CXXFLAGS ?= -std=c++17 -O3 -march=native -Wall -Wextra -pedantic -fopenmp
BIN = bin/lid_cavity_openmp
OMP_NUM_THREADS ?= 4

.PHONY: build run smoke quick scaling plot clean

build:
	mkdir -p bin
	$(CXX) $(CXXFLAGS) src/lid_cavity.cpp -o $(BIN)

run: build
	OMP_NUM_THREADS=$(OMP_NUM_THREADS) $(BIN) --single --N $(or $(N),64) --Re $(or $(RE),100) --scheme $(or $(SCHEME),central) --pressure $(or $(PRESSURE),RBGS)

smoke: build
	OMP_NUM_THREADS=$(OMP_NUM_THREADS) $(BIN) --mode smoke

quick: build
	OMP_NUM_THREADS=$(OMP_NUM_THREADS) $(BIN) --mode quick

scaling: build
	@mkdir -p results/scaling
	@echo "Threads,Runtime_s" > results/scaling/openmp_scaling.csv
	@for t in 1 2 4 8; do \
	  echo "threads=$$t"; \
	  /usr/bin/time -f "$$t,%e" -a -o results/scaling/openmp_scaling.csv env OMP_NUM_THREADS=$$t $(BIN) --mode smoke >/dev/null; \
	done

plot:
	python3 postprocess/plot_results.py --all-cases --summaries all

clean:
	rm -rf bin results/data results/figures results/scaling
	mkdir -p results
	touch results/.gitkeep
