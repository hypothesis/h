Testing
=======

This section covers running and writing tests for the ``h`` codebase.

.. _running-the-tests:

Running the tests, linters and code formatters
----------------------------------------------

To run the unit tests (both backend and frontend) run:

.. code-block:: shell

   make test

To run the functional tests:

.. code-block:: shell

   make functests

To format your code correctly:

.. code-block:: shell

   make format

To run the linter:

.. code-block:: shell

   make lint

For many more useful ``make`` commands see:

.. code-block:: shell

   make help

Running the backend tests only
##############################

To run the backend test suite only call ``tox`` directly. For example:

.. code-block:: shell

   # Run the backend unit tests:
   tox

   # Run the backend functional tests:
   tox -qe functests

   # Run only one test directory or test file:
   tox tests/unit/h/models/annotation_test.py
   tox -qe functests tests/functional/api/test_profile.py

   # To pass arguments to pytest put them after a `--`:
   tox -- --exitfirst --pdb --failed-first tests/unit/h
   tox -qe functests -- --exitfirst --pdb --failed-first tests/functional

   # See all of pytest's command line options:
   tox -- -h

Running the frontend tests only
###############################

To run the frontend test suite only, run the appropriate test task with gulp.
For example:

.. code-block:: shell

    make gulp args=test

When working on the front-end code, you can run the Karma test runner in
auto-watch mode which will re-run the tests whenever a change is made to the
source code. To start the test runner in auto-watch mode, run:

.. code-block:: shell

    make gulp args=test-watch

To run only a subset of tests for front-end code, use the ``--grep``
argument or mocha's `.only()`_ modifier.

.. code-block:: shell

    make gulp args=test-watch --grep <pattern>

.. _.only(): http://jaketrent.com/post/run-single-mocha-test/

Writing tests
-------------

Sean Hammond has written up a `guide to getting started`_ running and writing
our tests, which covers some of the tools we use (``tox`` and ``pytest``) and
some of the testing techniques they provide (factories and parametrization).

.. _guide to getting started: https://www.seanh.cc/post/running-the-h-tests

Unit and functional tests
#########################

We keep our functional tests separate from our unit tests, in the
``tests/functional`` directory. Because these are slow to run, we will usually
write one or two functional tests to check a new feature works in the common
case, and unit tests for all the other cases.

Using mock objects
##################

The ``mock`` library lets us construct fake versions of our objects to help with
testing. While this can make it easier to write fast, isolated tests, it also
makes it easier to write tests that don't reflect reality.

In an ideal world, we would always be able to use real objects instead of stubs
or mocks, but sometimes this can result in:

- complicated test setup code
- slow tests
- coupling of test assertions to non-interface implementation details

For new code, it's usually a good idea to design the code so that it's easy to
test with "real" objects, rather than stubs or mocks. It can help to make
extensive use of `value objects`_ in tested interfaces (using
``collections.namedtuple`` from the standard library, for example) and apply
the `functional core, imperative shell`_ pattern.

For older code which doesn't make testing so easy, or for code that is part of
the "imperative shell" (see link in previous paragraph) it can sometimes be
hard to test what you need without resorting to stubs or mock objects, and
that's fine.

.. _value objects: https://martinfowler.com/bliki/ValueObject.html
.. _functional core, imperative shell: https://www.destroyallsoftware.com/talks/boundaries
