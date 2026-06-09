PYTHON ?= python3
NP ?= 4

.PHONY: install run smoke quick clean

install:
	$(PYTHON) -m pip install -r requirements.txt

run: smoke

smoke:
	mpirun -np $(NP) $(PYTHON) src/mpi_case_driver.py --mode smoke --no-fields

quick:
	mpirun -np $(NP) $(PYTHON) src/mpi_case_driver.py --mode quick --no-fields

clean:
	rm -rf results/data results/mpi_raw __pycache__ src/__pycache__
	mkdir -p results
	touch results/.gitkeep
