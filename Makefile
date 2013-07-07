SHELL := bash

ifndef VIRTUAL_ENV
    python = "bin/python"
else
    python = `which python`
endif

test: functional_test unit_test

functional_test: 
	if [ -f "pyramid.pid" ] ; then $(python) bin/pserve --stop-daemon ; fi
	rm -f test.db
	echo "starting test h instance" 
	$(python) run test.ini --daemon
	$(python) -m pytest tests/functional

unit_test: 
	rm -f test.db
	$(python) -m pytest tests/unit

