SHELL := bash

ifndef VIRTUAL_ENV
    python = "bin/python"
else
    python = `which python`
endif

test: functional_test unit_test

functional_test: 
	echo "python=${python}"
	if [ -f "test.pid" ] ; then $(python) bin/pserve --stop-daemon --pid-file=test.pid; fi
	rm -f test.db
	echo "starting test h instance" 
	$(python) run test.ini --daemon --pid-file=test.pid
	$(python) -m pytest tests/functional

unit_test: 
	rm -f test.db
	$(python) -m pytest tests/unit

