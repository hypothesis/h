PATH := $(shell pwd)/bin:$(PATH)
SHELL := /bin/bash
NPM_BIN := $(shell npm bin)
DOCKER_TAG = dev

# Unless the user has specified otherwise in their environment, it's probably a
# good idea to refuse to install unless we're in an activated virtualenv.
ifndef PIP_REQUIRE_VIRTUALENV
PIP_REQUIRE_VIRTUALENV = 1
endif
export PIP_REQUIRE_VIRTUALENV

.PHONY: default
default: test

build/manifest.json: node_modules/.uptodate
	$(NPM_BIN)/gulp build

## Clean up runtime artifacts (needed after a version update)
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -f node_modules/.uptodate .pydeps
	rm -rf build

## Run the development H server locally
.PHONY: dev
dev: build/manifest.json .pydeps
	@hypothesis devserver

## Build hypothesis/hypothesis docker image
.PHONY: docker
docker:
	git archive HEAD | docker build -t hypothesis/hypothesis:$(DOCKER_TAG) -

## Run test suite
.PHONY: test
test: node_modules/.uptodate
	@pip install -q tox
	tox
	$(NPM_BIN)/gulp test

################################################################################

# Fake targets to aid with deps installation
.pydeps: setup.py requirements.txt
	@echo installing python dependencies
	@pip install --use-wheel -r requirements-dev.in tox
	@touch $@

node_modules/.uptodate: package.json
	@echo installing javascript dependencies
	@$(NPM_BIN)/check-dependencies 2>/dev/null || npm install
	@touch $@

# Self documenting Makefile
.PHONY: help
help:
	@echo "The following targets are available:"
	@echo " clean      Clean up runtime artifacts (needed after a version update)"
	@echo " dev        Run the development H server locally"
	@echo " docker     Build hypothesis/hypothesis docker image"
	@echo " test       Run the test suite (default)"
