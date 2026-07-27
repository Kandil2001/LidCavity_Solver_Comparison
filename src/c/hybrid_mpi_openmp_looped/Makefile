CC ?= mpicc
CFLAGS ?= -O3 -std=c11 -Wall -Wextra -fopenmp
NP ?= 4
OMP_NUM_THREADS ?= 2
N ?= 64
RE ?= 100
STEPS ?= 2000
POISSON_ITERS ?= 250
SCHEME ?= upwind
POISSON_SOLVER ?= RBGS
SOR_OMEGA ?= 1.7
NO_FIELDS ?= 1
NO_FIELDS_FLAG := $(if $(filter 1 true yes,$(NO_FIELDS)),--no-fields,)
TARGET = bin/hybrid_mpi_openmp_looped
SRC = src/hybrid_lid_cavity.c

.PHONY: all build smoke quick run clean

all: build

build:
	mkdir -p bin results/data results/figures
	$(CC) $(CFLAGS) $(SRC) -lm -o $(TARGET)

smoke: build
	OMP_NUM_THREADS=$(OMP_NUM_THREADS) mpirun -np $(NP) $(TARGET) --N 32 --Re 100 --steps 50 --poisson-iters 50 --scheme upwind --poisson-solver $(POISSON_SOLVER) --sor-omega $(SOR_OMEGA) --no-fields

quick: build
	OMP_NUM_THREADS=$(OMP_NUM_THREADS) mpirun -np $(NP) $(TARGET) --N $(N) --Re $(RE) --steps 1000 --poisson-iters $(POISSON_ITERS) --scheme $(SCHEME) --poisson-solver $(POISSON_SOLVER) --sor-omega $(SOR_OMEGA) $(NO_FIELDS_FLAG)

run: build
	OMP_NUM_THREADS=$(OMP_NUM_THREADS) mpirun -np $(NP) $(TARGET) --N $(N) --Re $(RE) --steps $(STEPS) --poisson-iters $(POISSON_ITERS) --scheme $(SCHEME) --poisson-solver $(POISSON_SOLVER) --sor-omega $(SOR_OMEGA) $(NO_FIELDS_FLAG)

clean:
	rm -rf bin results/data/*.csv
