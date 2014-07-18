SHELL := bash
PATH := bin:${PATH}

default:
	@yes | ./bootstrap

clean:
	find h/static/scripts \
		-iname '*.js' \
		-path './vendor' -prune \
		-exec rm {} \;
	find h/static/styles \
		-iname '*.css' \
		-not -iname 'icomoon.css' \
		-not -iname 'visualsearch.css' \
		-not -iname 'jquery-ui-smoothness.css' \
		-exec rm {} \;

test:
	@echo -n "Checking to see if elasticsearch is running..."
	$(eval es := $(shell wget --quiet --output-document - http://localhost:9200))
	@if [ -n '${es}' ] ; then echo "yes." ; else echo "no!"; exit 1; fi
	python setup.py test
	hypothesis assets development.ini
	"$$(npm bin)"/karma start karma.config.js --single-run

.PHONY: clean test
