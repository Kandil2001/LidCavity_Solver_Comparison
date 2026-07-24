CXX ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra -pedantic -g0
NO_FIELDS ?= 0
NO_FIELDS_FLAG := $(if $(filter 1 true yes,$(NO_FIELDS)),--no-fields,)
BIN = bin/lid_cavity

.PHONY: build run smoke quick medium full paper paper-single plot clean

build:
	mkdir -p bin
	$(CXX) $(CXXFLAGS) src/lid_cavity.cpp -o $(BIN) -lstdc++fs

run: build
	$(BIN) --single --N $(or $(N),64) --Re $(or $(RE),100) --scheme $(or $(SCHEME),central) --pressure $(or $(PRESSURE),RBGS) $(NO_FIELDS_FLAG)

smoke: build
	$(BIN) --mode smoke $(NO_FIELDS_FLAG)

quick: build
	$(BIN) --mode quick $(NO_FIELDS_FLAG)

medium: build
	$(BIN) --mode medium $(NO_FIELDS_FLAG)

full: build
	$(BIN) --mode full $(NO_FIELDS_FLAG)

paper: build
	$(BIN) --mode paper $(NO_FIELDS_FLAG)

paper-single: build
	$(BIN) --single --N $(or $(N),65) --Re $(or $(RE),100) --scheme $(or $(SCHEME),central) --pressure $(or $(PRESSURE),RBSOR) --paper-protocol $(NO_FIELDS_FLAG)

plot:
	python3 postprocess/plot_results.py --all-cases --summaries all

clean:
	rm -rf bin results/data results/figures results/scaling results/logs results/mpi_raw __pycache__ src/__pycache__
	mkdir -p results/data results/figures results/scaling results/logs
	touch results/.gitkeep results/data/.gitkeep results/figures/.gitkeep results/scaling/.gitkeep results/logs/.gitkeep
