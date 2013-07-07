SHELL := bash

test: functional_test unit_test

functional_test: 
	if [ -f "pyramid.pid" ] ; then bin/python bin/pserve --stop-daemon ; fi
	rm -f test.db
	echo "starting test h instance" 
	bin/python run test.ini --daemon
	bin/python -m pytest tests/functional

unit_test: 
	bin/python -m pytest tests/unit

