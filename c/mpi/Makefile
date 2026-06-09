CC ?= gcc
MPICC ?= mpicc
CFLAGS ?= -std=c99 -O3 -march=native -Wall -Wextra
NP ?= 4
SOLVER = bin/lid_cavity_c
DRIVER = bin/mpi_case_driver

.PHONY: build run smoke quick merge clean

build:
	mkdir -p bin
	$(CC) $(CFLAGS) src/lid_cavity.c -lm -o $(SOLVER)
	$(MPICC) -std=c99 -O2 -Wall -Wextra src/mpi_case_driver.c -o $(DRIVER)

run: smoke

smoke: build
	mpirun -np $(NP) $(DRIVER) --mode smoke --solver ./$(SOLVER)
	python3 tools/merge_mpi_results.py

quick: build
	mpirun -np $(NP) $(DRIVER) --mode quick --solver ./$(SOLVER)
	python3 tools/merge_mpi_results.py

merge:
	python3 tools/merge_mpi_results.py

clean:
	rm -rf bin results/data results/mpi_raw
	mkdir -p results
	touch results/.gitkeep
