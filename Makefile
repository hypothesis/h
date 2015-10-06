SHELL := bash
PATH := bin:${PATH}
NPM_BIN = "$$(npm bin)"

# Unless the user has specified otherwise in their environment, it's probably a
# good idea to refuse to install unless we're in an activated virtualenv.
ifndef PIP_REQUIRE_VIRTUALENV
PIP_REQUIRE_VIRTUALENV = 1
endif
export PIP_REQUIRE_VIRTUALENV

default: deps

deps: .eggs/.uptodate node_modules/.uptodate

.eggs/.uptodate: setup.py requirements.txt
	pip install --use-wheel -e .[dev,testing,YAML]
	touch $@

node_modules/.uptodate: package.json
	npm install
	touch $@

clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf h/static/webassets-external
	rm -f h/static/scripts/vendor/*.min.js
	rm -f h/static/scripts/account.*js
	rm -f h/static/scripts/app.*js
	rm -f h/static/scripts/config.*js
	rm -f h/static/scripts/hypothesis.*js
	rm -f h/static/styles/*.css
	rm -f .coverage
	rm -f node_modules/.uptodate .eggs/.uptodate

dev: deps
	@gunicorn --reload --paste conf/development.ini

test: backend-test client-test

backend-test:
	@python setup.py test

client-test:
	@$(NPM_BIN)/karma start h/static/scripts/karma.config.js --single-run
	@$(NPM_BIN)/karma start h/browser/chrome/karma.config.js --single-run

client-test-watch:
	@$(NPM_BIN)/karma start h/static/scripts/karma.config.js

cover:
	@python setup.py test --cov
	@"$$(npm bin)"/karma start h/static/scripts/karma.config.js --single-run
	@"$$(npm bin)"/karma start h/browser/chrome/karma.config.js --single-run

lint:
	@prospector

.PHONY: clean cover deps dev lint test
