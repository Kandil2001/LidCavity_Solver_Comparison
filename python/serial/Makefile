PYTHON ?= python3

.PHONY: install run smoke quick plot clean

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) src/lid_cavity.py --single --N $(or $(N),64) --Re $(or $(RE),100) --scheme $(or $(SCHEME),central) --pressure $(or $(PRESSURE),RBGS)

smoke:
	$(PYTHON) src/lid_cavity.py --mode smoke

quick:
	$(PYTHON) src/lid_cavity.py --mode quick

plot:
	$(PYTHON) postprocess/plot_results.py --all-cases --summaries all

clean:
	rm -rf results/data results/figures __pycache__ src/__pycache__
	mkdir -p results
	touch results/.gitkeep
