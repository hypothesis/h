SHELL := bash
PATH := bin:${PATH}

clean:
	find h/js -iname '*.js' | xargs rm
	find h/css -iname '*.css' | xargs rm

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
