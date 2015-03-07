SHELL := bash
PATH := bin:${PATH}

default: deps

deps:
	@npm install
	@pip install -qU pip
	@pip install -q --use-wheel -e .[dev,testing,YAML]

clean:
	@rm -rf h/static/.webassets-cache
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	find h/static/scripts -mindepth 1 -name '*.min.js' -delete
	find h/static/styles -mindepth 1 -name '*.css' -delete

dev: deps
	@gunicorn --reload --paste development.ini

test: deps
	@echo -n "Checking to see if elasticsearch is running..."
	$(eval es := $(shell wget --quiet --output-document - http://localhost:9200))
	@if [ -n '${es}' ] ; then echo "yes." ; else echo "no!"; exit 1; fi
	@python setup.py test
	@"$$(npm bin)"/karma start h/static/scripts/karma.config.js --single-run
	@"$$(npm bin)"/karma start h/browser/chrome/karma.config.js --single-run

cover:
	@python setup.py test --cov

lint:
	@prospector

.PHONY: clean test
