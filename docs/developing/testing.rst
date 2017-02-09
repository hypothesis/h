Testing
#######

This section covers writing tests for the ``h`` codebase.

Getting started
---------------

Sean Hammond has written up a `guide to getting started`_ running and writing
our tests, which covers some of the tools we use (``tox`` and ``pytest``) and
some of the testing techniques they provide (factories and parametrization).

.. _guide to getting started: https://www.seanh.cc/posts/running-the-h-tests

Unit and functional tests
-------------------------

We keep our functional tests separate from our unit tests, in the
``tests/functional`` directory. Because these are slow to run, we will usually
write one or two functional tests to check a new feature works in the common
case, and unit tests for all the other cases.

Using mock objects
------------------

The ``mock`` library lets us construct fake versions of our objects to help with
testing. While this can make it easier to write fast, isolated tests, it also
makes it easier to write tests that don't reflect reality.

Where practical, we prefer to write tests using (in order of preference):

1. Real objects
2. Fake objects
3. Mock objects constructed with ``spec_set`` or ``autospec`` – these objects
   will only respond to the same methods as the real objects they replace,
   which reduces the risk of mocks that do not behave like their real
   counterparts
4. Generic mock objects

This is a deliberate decision that, when we have to choose between test
isolation and test fidelity, we usually want to choose test fidelity.
