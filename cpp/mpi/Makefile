CXX ?= g++
MPICC ?= mpicc
CXXFLAGS ?= -std=c++17 -O3 -march=native -Wall -Wextra -pedantic
NP ?= 4
SOLVER = bin/lid_cavity
DRIVER = bin/mpi_case_driver

.PHONY: build run smoke quick medium full merge clean

build:
	mkdir -p bin
	$(CXX) $(CXXFLAGS) src/lid_cavity.cpp -o $(SOLVER)
	$(MPICC) -std=c99 -O2 -Wall -Wextra src/mpi_case_driver.c -o $(DRIVER)

run: smoke

smoke: build
	mpirun -np $(NP) $(DRIVER) --mode smoke --solver ./$(SOLVER)
	python3 tools/merge_mpi_results.py

quick: build
	mpirun -np $(NP) $(DRIVER) --mode quick --solver ./$(SOLVER)
	python3 tools/merge_mpi_results.py

medium: build
	mpirun -np $(NP) $(DRIVER) --mode medium --solver ./$(SOLVER)
	python3 tools/merge_mpi_results.py

full: build
	mpirun -np $(NP) $(DRIVER) --mode full --solver ./$(SOLVER)
	python3 tools/merge_mpi_results.py

merge:
	python3 tools/merge_mpi_results.py

clean:
	rm -rf bin results/data results/figures results/scaling results/logs results/mpi_raw __pycache__ src/__pycache__
	mkdir -p results/data results/figures results/scaling results/logs
	touch results/.gitkeep results/data/.gitkeep results/figures/.gitkeep results/scaling/.gitkeep results/logs/.gitkeep
