PYTHON ?= python3
NO_FIELDS ?= 0
NO_FIELDS_FLAG := $(if $(filter 1 true yes,$(NO_FIELDS)),--no-fields,)

.PHONY: install run smoke quick medium full plot clean

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) src/lid_cavity.py --single --N $(or $(N),64) --Re $(or $(RE),100) --scheme $(or $(SCHEME),central) --pressure $(or $(PRESSURE),RBGS)

smoke:
	$(PYTHON) src/lid_cavity.py --mode smoke $(NO_FIELDS_FLAG)

quick:
	$(PYTHON) src/lid_cavity.py --mode quick $(NO_FIELDS_FLAG)

medium:
	$(PYTHON) src/lid_cavity.py --mode medium $(NO_FIELDS_FLAG)

full:
	$(PYTHON) src/lid_cavity.py --mode full $(NO_FIELDS_FLAG)

plot:
	$(PYTHON) postprocess/plot_results.py --all-cases --summaries all

clean:
	rm -rf bin results/data results/figures results/scaling results/logs results/mpi_raw __pycache__ src/__pycache__
	mkdir -p results/data results/figures results/scaling results/logs
	touch results/.gitkeep results/data/.gitkeep results/figures/.gitkeep results/scaling/.gitkeep results/logs/.gitkeep
