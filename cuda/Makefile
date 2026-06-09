NVCC ?= nvcc
BIN = bin/lid_cavity_cuda

.PHONY: build run smoke clean

build:
	mkdir -p bin
	$(NVCC) -O3 -std=c++17 src/lid_cavity_cuda.cu -o $(BIN)

run: build
	$(BIN) --N $(or $(N),64) --Re $(or $(RE),100) --scheme $(or $(SCHEME),upwind) --maxIter $(or $(MAX_ITER),500) --poisson-maxIter $(or $(POISSON_ITER),300)

smoke: build
	$(BIN) --mode smoke

clean:
	rm -rf bin results/data results/figures
	mkdir -p results
	touch results/.gitkeep
