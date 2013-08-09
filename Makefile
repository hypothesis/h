SHELL := bash
PATH := bin:${PATH}

test: elasticsearch functional_test unit_test

functional_test: 
	@echo "running functional tests"

	# stop the test daemon if it is running
	if [ -f "test.pid" ] ; then pserve --stop-daemon --pid-file=test.pid; fi

	# start with clean test db
	rm -f test.db

	# start the test instance of h
	python run test.ini --daemon --pid-file=test.pid

	# run the functional tests
	python -m pytest tests/functional/

	# stop h
	pserve --stop-daemon --pid-file=test.pid

unit_test: 
	@echo "running unit tests"

	rm -f test.db
	python -m pytest tests/unit

elasticsearch:
	@echo "elasticsearch running?"
	$(eval es := $(shell wget --quiet --output-document - http://localhost:9200))
	if [ -n '${es}' ] ; then echo "elasticsearch running" ; else echo "please start elasticsearch"; exit 1; fi
