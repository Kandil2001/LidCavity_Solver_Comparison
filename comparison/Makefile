PYTHON ?= python3

.PHONY: install compare report clean

install:
	$(PYTHON) -m pip install -r requirements.txt

compare:
	$(PYTHON) compare_outputs.py --help

report:
	$(PYTHON) benchmark_report.py --help

clean:
	rm -rf results/data results/figures results/scaling results/logs
	mkdir -p results/data results/figures results/scaling results/logs
	touch results/.gitkeep results/data/.gitkeep results/figures/.gitkeep results/scaling/.gitkeep results/logs/.gitkeep
