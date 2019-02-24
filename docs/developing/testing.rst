Testing
=======

This section covers writing tests for the ``h`` codebase.

Getting started
---------------

Sean Hammond has written up a `guide to getting started`_ running and writing
our tests, which covers some of the tools we use (``tox`` and ``pytest``) and
some of the testing techniques they provide (factories and parametrization).

.. _guide to getting started: https://www.seanh.cc/post/running-the-h-tests

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
