SHELL := bash
PATH := bin:${PATH}

default:
	@yes | ./bootstrap

clean:
	find h/js -iname '*.js' | xargs -r rm
	find h/css -iname '*.css' | sed /visualsearch/d | xargs -r rm

test:
	@echo -n "Checking to see if elasticsearch is running..."
	$(eval es := $(shell wget --quiet --output-document - http://localhost:9200))
	@if [ -n '${es}' ] ; then echo "yes." ; else echo "no!"; exit 1; fi
	hypothesis assets test.ini
	python setup.py test

.PHONY: clean test
