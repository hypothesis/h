PATH := bin:${PATH}
NPM_BIN := $(shell npm bin)
ISODATE := $(shell TZ=UTC date '+%Y%m%d')
BUILD_ID := $(shell python -c 'import h; print(h.__version__)')
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
	rm -f node_modules/.uptodate h.egg-info/.uptodate
	rm -rf build dist

## Run the development H server locally
.PHONY: dev
dev: build/manifest.json h.egg-info/.uptodate
	@hypothesis devserver

.PHONY: dist
dist: dist/h-$(BUILD_ID).tar.gz

dist/h-$(BUILD_ID).tar.gz:
	python setup.py sdist

dist/h-$(BUILD_ID): dist/h-$(BUILD_ID).tar.gz
	tar -C dist -zxf $<

## Build hypothesis/hypothesis docker image
.PHONY: docker
docker: dist/h-$(BUILD_ID)
	docker build -t hypothesis/hypothesis:$(DOCKER_TAG) $<

## Run test suite
.PHONY: test
test: node_modules/.uptodate
	@pip install -q tox
	tox
	$(NPM_BIN)/gulp test-app

################################################################################

# Fake targets to aid with deps installation
h.egg-info/.uptodate: setup.py requirements.txt
	@echo installing python dependencies
	@pip install --use-wheel -e .[dev] tox
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
