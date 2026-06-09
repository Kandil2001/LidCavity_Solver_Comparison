PYTHON ?= python3

.PHONY: install compare report clean

install:
	$(PYTHON) -m pip install -r requirements.txt

compare:
	$(PYTHON) compare_outputs.py --help

report:
	$(PYTHON) benchmark_report.py --help

clean:
	rm -rf results
	mkdir -p results
	touch results/.gitkeep
