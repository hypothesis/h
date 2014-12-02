SHELL := bash
PATH := bin:${PATH}

default:
	@yes | ./bootstrap

clean:
	@rm -rf h/static/.sass-cache
	@rm -rf h/static/.webassets-cache
	find h/static/scripts \
		-path 'h/static/scripts/vendor' -prune \
		-o -iname '*.js' \
		-exec rm {} \;
	find h/static/styles \
		-iname '*.css' \
		-prune -o -iname 'icomoon.css' \
		-exec rm {} \;

test:
	@echo -n "Checking to see if elasticsearch is running..."
	$(eval es := $(shell wget --quiet --output-document - http://localhost:9200))
	@if [ -n '${es}' ] ; then echo "yes." ; else echo "no!"; exit 1; fi
	python setup.py develop test
	hypothesis assets development.ini
	"$$(npm bin)"/karma start karma.config.js --single-run
	"$$(npm bin)"/karma start h/browser/chrome/karma.config.js --single-run

.PHONY: clean test
