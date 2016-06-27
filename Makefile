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

## Build the python H distribution
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
	$(NPM_BIN)/gulp test-extension

################################################################################

# Extension build
.PHONY: extensions
extensions: build/$(ISODATE)-$(BUILD_ID)-chrome-stage.zip
extensions: build/$(ISODATE)-$(BUILD_ID)-chrome-prod.zip
extensions: build/$(ISODATE)-$(BUILD_ID)-firefox-stage.xpi
extensions: build/$(ISODATE)-$(BUILD_ID)-firefox-prod.xpi

build/%-chrome-stage.zip: build/manifest.json
	@rm -rf build/chrome $@
	hypothesis-buildext chrome \
		--service 'https://stage.hypothes.is' \
		--websocket 'wss://stage.hypothes.is/ws' \
		--sentry-public-dsn '$(SENTRY_DSN_STAGE)' \
		--bouncer 'https://bouncer-stage.hypothes.is'
	@zip -qr $@ build/chrome

build/%-chrome-prod.zip: build/manifest.json
	@rm -rf build/chrome $@
	hypothesis-buildext chrome \
		--service 'https://hypothes.is' \
		--websocket 'wss://hypothes.is/ws' \
		--sentry-public-dsn '$(SENTRY_DSN_PROD)' \
		--bouncer 'https://hyp.is'
	@zip -qr $@ build/chrome

build/%-firefox-stage.xpi: build/manifest.json
	@rm -rf build/firefox $@
	hypothesis-buildext firefox \
		--service 'https://stage.hypothes.is' \
		--websocket 'wss://stage.hypothes.is/ws' \
		--sentry-public-dsn '$(SENTRY_DSN_STAGE)' \
		--bouncer 'https://bouncer-stage.hypothes.is'
	@cd build/firefox && zip -qr $(abspath $@) .

build/%-firefox-prod.xpi: build/manifest.json
	@rm -rf build/firefox $@
	hypothesis-buildext firefox \
		--service 'https://hypothes.is' \
		--websocket 'wss://hypothes.is/ws' \
		--sentry-public-dsn '$(SENTRY_DSN_PROD)' \
		--bouncer 'https://hyp.is'
	@cd build/firefox && zip -qr $(abspath $@) .

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
	@echo
	@echo " clean      Clean up runtime artifacts (needed after a version update)"
	@echo " dev        Run the development H server locally"
	@echo " dist       Build the python H distribution"
	@echo " docker     Build hypothesis/hypothesis docker image"
	@echo " extensions Build the browser extensions"
	@echo " test       Run the test suite (default)"
	@echo
	@echo "To run the test suite and build the whole app, you can do:"
	@echo " $ make clean && make && make dist && make extensions"
