SHELL := bash
PATH := bin:${PATH}

# Unless the user has specified otherwise in their environment, it's probably a
# good idea to refuse to install unless we're in an activated virtualenv.
ifndef PIP_REQUIRE_VIRTUALENV
PIP_REQUIRE_VIRTUALENV = 1
endif
export PIP_REQUIRE_VIRTUALENV

default: deps

h.egg-info: setup.py
	@pip install -q --use-wheel -e .[dev,testing,YAML]
	@touch h.egg-info

node_modules: package.json
	@npm install
	@touch node_modules

deps: h.egg-info node_modules

clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	find h/static/scripts -mindepth 1 -name '*.min.js' -delete
	find h/static/styles -mindepth 1 -name '*.css' -delete

dev: deps
	@gunicorn --reload --paste conf/development.ini

test:
	@python setup.py test
	@"$$(npm bin)"/karma start h/static/scripts/karma.config.js --single-run
	@"$$(npm bin)"/karma start h/browser/chrome/karma.config.js --single-run

cover:
	@python setup.py test --cov

lint:
	@prospector
	@jscs .

.PHONY: clean cover deps dev lint test
