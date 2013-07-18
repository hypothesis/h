SHELL := bash

ifndef VIRTUAL_ENV
    python = "bin/python"
else
    python = `which python`
endif

ifdef TRAVIS
    pserve = "pserve"
else
    pserve = "bin/pserve"
endif

test: functional_test unit_test

functional_test: 
	# stop the test daemon if it is running
	if [ -f "test.pid" ] ; then $(python) $(pserve) --stop-daemon --pid-file=test.pid; fi

	# start with clean test db
	rm -f test.db

	# start the test instance of h
	$(python) run test.ini --daemon --pid-file=test.pid

	# run the functional tests
	$(python) -m pytest tests/functional/

	# stop h
	$(python) $(pserve) --stop-daemon --pid-file=test.pid

unit_test: 
	rm -f test.db
	$(python) -m pytest tests/unit

