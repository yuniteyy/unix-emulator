PYTHON ?= python3
export PYTHONPATH := src

.PHONY: run test lint demo

run:
	$(PYTHON) -m vfs_shell $(ARGS)

test:
	$(PYTHON) -m unittest discover -s tests -v

lint:
	$(PYTHON) -m flake8 src tests

demo:
	sh scripts/run_all.sh
