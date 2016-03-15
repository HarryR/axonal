mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(dir $(mkfile_path))
PYTHON35=PYTHONPATH=$(current_dir) python3.5
FLAKE8=$(PYTHON35) -m flake8
PYLINT=$(PYTHON35) -m pylint
PYTEST=$(PYTHON35) -m pytest

all:
	@echo make test

test:
	$(PYTEST)

clean:
	find ./ -name '__pycache__' | xargs rm -rf
	find ./ -name '.cache' | xargs rm -rf

lint:
	PYTHONPATH=$(current_dir) $(FLAKE8) axonal
	PYTHONPATH=$(current_dir) $(PYLINT) axonal