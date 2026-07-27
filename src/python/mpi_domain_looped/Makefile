PYTHON ?= python3
NP ?= 4
N ?= 64
RE ?= 100
STEPS ?= 2000
POISSON_ITERS ?= 250
SCHEME ?= upwind
POISSON_SOLVER ?= RBGS
SOR_OMEGA ?= 1.7
NO_FIELDS ?= 1
NO_FIELDS_FLAG := $(if $(filter 1 true yes,$(NO_FIELDS)),--no-fields,)

.PHONY: smoke quick run clean

smoke:
	mpirun -np $(NP) $(PYTHON) solver.py --N 32 --Re 100 --steps 30 --poisson-iters 30 --scheme upwind --poisson-solver $(POISSON_SOLVER) --sor-omega $(SOR_OMEGA) --no-fields

quick:
	mpirun -np $(NP) $(PYTHON) solver.py --N $(N) --Re $(RE) --steps 500 --poisson-iters $(POISSON_ITERS) --scheme $(SCHEME) --poisson-solver $(POISSON_SOLVER) --sor-omega $(SOR_OMEGA) $(NO_FIELDS_FLAG)

run:
	mpirun -np $(NP) $(PYTHON) solver.py --N $(N) --Re $(RE) --steps $(STEPS) --poisson-iters $(POISSON_ITERS) --scheme $(SCHEME) --poisson-solver $(POISSON_SOLVER) --sor-omega $(SOR_OMEGA) $(NO_FIELDS_FLAG)

clean:
	rm -f results/data/*.csv
