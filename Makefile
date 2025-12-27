# Makefile
SHELL := /usr/bin/zsh

# Uses whichever python/pip is active
PYTHON      ?= python
PIP		 ?= pip
PIP_COMPILE ?= pip-compile

# Fixed base constraints
CORE_CONSTRAINT := $(HOME)/env-specs/ds-core/requirements.txt

# Project deps
REQ_IN   ?= requirements.extra.in
REQ_LOCK ?= requirements.extra.txt

# App config
CFG ?= configs/download.yaml

# Ensure src/ imports work without packaging
export PYTHONPATH := $(PWD)/src:$(PYTHONPATH)

.PHONY: help check init compile install download download-fast clean

help:
	@echo "Targets:"
	@echo "  make init		    Create the agreed folder structure + placeholder files (non-destructive)"
	@echo "  make check		   Verify python/pip/pip-compile + ds-core constraint file exists"
	@echo "  make compile		 Generate $(REQ_LOCK) from $(REQ_IN) constrained by ds-core"
	@echo "  make install		 pip install -r $(REQ_LOCK)"
	@echo "  make download		Run all enabled downloaders"
	@echo "  make download-fast   Like download but skips auth-heavy sources (ERA5/Comtrade)"
	@echo "  make clean		   Remove data_raw/* and logs/* (keeps folders)"

check:
	@echo "python:  $$($(PYTHON) -c 'import sys; print(sys.executable)')"
	@echo "version: $$($(PYTHON) -c 'import sys; print(sys.version.split()[0])')"
	@echo "pip:     $$($(PIP) -V)"
	@$(PIP_COMPILE) --version >/dev/null 2>&1 || (echo "pip-compile not found. Activate ds-core (pyenv local ds-core)."; exit 1)
	@test -f "$(CORE_CONSTRAINT)" || (echo "Missing ds-core constraints: $(CORE_CONSTRAINT)"; exit 1)

# Creates folder tree + minimal starter files (won't overwrite existing content)
init:
	@$(PYTHON) scripts/bootstrap_repo.py

compile: check
	@test -f "$(REQ_IN)" || (echo "Missing $(REQ_IN). Run 'make init' first."; exit 1)
	@echo "Compiling $(REQ_LOCK) using constraints: $(CORE_CONSTRAINT)"
	$(PIP_COMPILE) $(REQ_IN) -c $(CORE_CONSTRAINT) -o $(REQ_LOCK)

install: compile
	$(PIP) install -r $(REQ_LOCK)

points: install
	$(PYTHON) scripts/build_points_from_boundaries.py

download: install
	$(PYTHON) -m maize_data.cli download --config $(CFG)

download-fast: install
	$(PYTHON) -m maize_data.cli download --config $(CFG) --skip-auth

clean:
	rm -rf data_raw/* logs/*
	@mkdir -p data_raw logs
	@touch data_raw/.gitkeep logs/.gitkeep
