SHELL := bash
PATH := bin:${PATH}

default:
	./bootstrap

clean:
	find h/js -iname '*.js' | xargs -r rm
	find h/css -iname '*.css' | sed /visualsearch/d | xargs -r rm

test: elasticsearch
	hypothesis assets test.ini
	python setup.py test

elasticsearch:
	@echo -n "Checking to see if elasticsearch is running..."
	$(eval es := $(shell wget --quiet --output-document - http://localhost:9200))
	@if [ -n '${es}' ] ; then echo "yes." ; else echo "no!"; exit 1; fi

.PHONY: clean test functional_test unit_test elasticsearch
