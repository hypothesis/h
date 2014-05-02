SHELL := bash
PATH := bin:${PATH}

default:
	./bootstrap

clean:
	find h/js -iname '*.js' | xargs -r rm
	find h/css -iname '*.css' | sed /visualsearch/d | xargs -r rm

test: elasticsearch functional_test unit_test

functional_test:
ifneq ($(TRAVIS_SECURE_ENV_VARS),false)
	@echo "running functional tests"
	# ensure the assets are built
	hypothesis assets test.ini
	# run the functional tests
	py.test tests/functional/
endif

unit_test:
	@echo "running unit tests"
	py.test tests/unit

elasticsearch:
	@echo "elasticsearch running?"
	$(eval es := $(shell wget --quiet --output-document - http://localhost:9200))
	@if [ -n '${es}' ] ; then echo "elasticsearch running" ; else echo "please start elasticsearch"; exit 1; fi

.PHONY: clean test functional_test unit_test elasticsearch
