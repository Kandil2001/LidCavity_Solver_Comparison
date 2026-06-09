PYTHON ?= python3
NP ?= 4

.PHONY: install run smoke quick medium full clean

install:
	$(PYTHON) -m pip install -r requirements.txt

run: smoke

smoke:
	mpirun -np $(NP) $(PYTHON) src/mpi_case_driver.py --mode smoke --no-fields

quick:
	mpirun -np $(NP) $(PYTHON) src/mpi_case_driver.py --mode quick --no-fields

medium:
	mpirun -np $(NP) $(PYTHON) src/mpi_case_driver.py --mode medium --no-fields

full:
	mpirun -np $(NP) $(PYTHON) src/mpi_case_driver.py --mode full --no-fields

clean:
	rm -rf bin results/data results/figures results/scaling results/logs results/mpi_raw __pycache__ src/__pycache__
	mkdir -p results/data results/figures results/scaling results/logs
	touch results/.gitkeep results/data/.gitkeep results/figures/.gitkeep results/scaling/.gitkeep results/logs/.gitkeep
