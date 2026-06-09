CC ?= gcc
CFLAGS ?= -std=c99 -O3 -Wall -Wextra
BIN = bin/lid_cavity_c

.PHONY: build run smoke quick plot clean

build:
	mkdir -p bin
	$(CC) $(CFLAGS) src/lid_cavity.c -lm -o $(BIN)

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
