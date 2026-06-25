NVCC ?= nvcc
BIN = bin/lid_cavity_cuda
N ?= 64
RE ?= 100
SCHEME ?= upwind
PRESSURE ?= JACOBI
MAX_ITER ?= 500
POISSON_ITER ?= 300
BLOCK_SIZE ?= 256
PYTHON ?= python3

.PHONY: build run smoke quick medium full scaling check-cuda clean

build:
	mkdir -p bin
	$(NVCC) -O3 -std=c++17 src/lid_cavity_cuda.cu -o $(BIN)

check-cuda:
	@command -v nvcc >/dev/null 2>&1 || { echo "nvcc not found"; exit 127; }
	@command -v nvidia-smi >/dev/null 2>&1 || { echo "nvidia-smi not found"; exit 127; }
	@nvidia-smi >/dev/null 2>&1 || { echo "No accessible NVIDIA GPU detected"; exit 1; }

run: build
	$(BIN) --N $(N) --Re $(RE) --scheme $(SCHEME) --pressure $(PRESSURE) --maxIter $(MAX_ITER) --poisson-maxIter $(POISSON_ITER) --block-size $(BLOCK_SIZE)

smoke: build
	$(BIN) --mode smoke --no-fields

quick: build
	$(BIN) --mode quick --no-fields

medium: build
	$(BIN) --mode medium --no-fields

full: build
	$(BIN) --mode full --no-fields

scaling:
	$(PYTHON) ../scripts/run_cuda_scaling.py --block-sizes $(or $(BLOCK_SIZES),64,128,256) --N $(N) --Re $(RE) --scheme $(SCHEME) --pressure $(PRESSURE)

clean:
	rm -rf bin results/data results/figures results/scaling results/logs results/mpi_raw __pycache__ src/__pycache__
	mkdir -p results/data results/figures results/scaling results/logs
	touch results/.gitkeep results/data/.gitkeep results/figures/.gitkeep results/scaling/.gitkeep results/logs/.gitkeep
