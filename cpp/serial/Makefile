CXX ?= g++
CXXFLAGS ?= -std=c++17 -O3 -march=native -Wall -Wextra -pedantic
BIN = bin/lid_cavity

.PHONY: build run smoke quick plot clean

build:
	mkdir -p bin
	$(CXX) $(CXXFLAGS) src/lid_cavity.cpp -o $(BIN)

run: build
	$(BIN) --single --N $(or $(N),64) --Re $(or $(RE),100) --scheme $(or $(SCHEME),central) --pressure $(or $(PRESSURE),RBGS)

smoke: build
	$(BIN) --mode smoke

quick: build
	$(BIN) --mode quick

plot:
	python3 postprocess/plot_results.py --all-cases --summaries all

clean:
	rm -rf bin results/data results/figures
	mkdir -p results
	touch results/.gitkeep
