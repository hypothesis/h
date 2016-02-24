PATH := bin:${PATH}
NPM_BIN = "$$(npm bin)"

ISODATE := $(shell TZ=UTC date '+%Y%m%d')
BUILD_ID := $(shell python -c 'import h; print(h.__version__)')

# Unless the user has specified otherwise in their environment, it's probably a
# good idea to refuse to install unless we're in an activated virtualenv.
ifndef PIP_REQUIRE_VIRTUALENV
PIP_REQUIRE_VIRTUALENV = 1
endif
export PIP_REQUIRE_VIRTUALENV

default: deps

deps: h.egg-info/.uptodate node_modules/.uptodate

h.egg-info/.uptodate: setup.py requirements.txt
	pip install --use-wheel -e .[dev,testing]
	touch $@

node_modules/.uptodate: package.json
	npm install
	touch $@

clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -f .coverage
	rm -f node_modules/.uptodate .eggs/.uptodate
	rm -rf build dist

dist: dist/h-$(BUILD_ID).tar.gz

dist/h-$(BUILD_ID).tar.gz:
	python setup.py sdist

dist/h-$(BUILD_ID): dist/h-$(BUILD_ID).tar.gz
	tar -C dist -zxf $<

docker: dist/h-$(BUILD_ID)
	docker build -t hypothesis/hypothesis:dev $<

dev: deps
	@gunicorn --reload --paste conf/development-app.ini

test: backend-test client-test

backend-test: deps
	@python setup.py test

client-test: client-app-test client-extension-test

client-app-test: deps
	@$(NPM_BIN)/karma start h/static/scripts/karma.config.js --single-run

client-app-test-watch: deps
	@$(NPM_BIN)/karma start h/static/scripts/karma.config.js

client-extension-test: deps
	@$(NPM_BIN)/karma start h/browser/chrome/karma.config.js --single-run

client-extension-test-watch: deps
	@$(NPM_BIN)/karma start h/browser/chrome/karma.config.js

client-assets: deps
	@NODE_ENV=production $(NPM_BIN)/gulp build

client-assets-dev: deps
	@$(NPM_BIN)/gulp build

client-assets-watch: deps
	@$(NPM_BIN)/gulp watch

cover:
	@python setup.py test --cov
	@"$$(npm bin)"/karma start h/static/scripts/karma.config.js --single-run
	@"$$(npm bin)"/karma start h/browser/chrome/karma.config.js --single-run

lint:
	@prospector

extensions: build/$(ISODATE)-$(BUILD_ID)-chrome-stage.zip
extensions: build/$(ISODATE)-$(BUILD_ID)-chrome-prod.zip

build/%-chrome-stage.zip:
	@rm -rf build/chrome $@
	hypothesis-buildext chrome \
		--service 'https://stage.hypothes.is' \
		--websocket 'wss://stage.hypothes.is/ws' \
		--sentry-public-dsn '$(SENTRY_DSN_STAGE)' \
		--bouncer 'https://hpt.is/*'
	@zip -qr $@ build/chrome

build/%-chrome-prod.zip:
	@rm -rf build/chrome $@
	hypothesis-buildext chrome \
		--service 'https://hypothes.is' \
		--websocket 'wss://hypothes.is/ws' \
		--sentry-public-dsn '$(SENTRY_DSN_PROD)' \
		--bouncer 'https://hpt.is/*'
	@zip -qr $@ build/chrome

.PHONY: clean cover deps dev dist docker extensions lint test
