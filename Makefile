PYTHON ?= python

.PHONY: test bench demo eval compare

test:
	$(PYTHON) tools/validate_defaults.py
	$(PYTHON) -m pytest -q

bench:
	$(PYTHON) -m tonesight_ns8.cli benchmark --suite core

demo:
	$(PYTHON) examples/ns8_drift_demo.py --out-root runs/demo

eval:
	$(PYTHON) -m tonesight_ns8.cli eval

compare:
	@echo "Usage: make compare RUN_A=runs/<baseline> RUN_B=runs/<candidate>"
	@test -n "$(RUN_A)" && test -n "$(RUN_B)"
	$(PYTHON) -m tonesight_ns8.cli compare $(RUN_A) $(RUN_B) --top-n 10 --write

