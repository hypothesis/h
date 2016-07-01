# -*- coding: utf-8 -*-

"""
Matchers for use in tests.

This module contains objects which can be used to write tests which are easier
to read, especially when using assertions against :py:class:`mock.Mock`
objects. Each matcher defines an __eq__ method, allowing instances of these
matchers to be used wherever you would usually pass a plain value.

For example, imagine you wanted to ensure that the `set_value` method of the
`foo` mock object was called exactly once with an integer. Previously you
would have to do something like:

    assert foo.set_value.call_count == 1
    assert isinstance(foo.set_value.call_args[0][0], int)

By using the `instance_of` matcher you can simply write:

    foo.set_value.assert_called_once_with(matchers.instance_of(int))

As a bonus, the second test will print substantially more useful debugging
output if it fails, e.g.

    E       AssertionError: Expected call: set_value(<instance of <type 'int'>>)
    E       Actual call: set_value('a string')

"""


class instance_of(object):
    """An object __eq__ to any object which is an instance of `type_`."""

    def __init__(self, type_):
        self.type = type_

    def __eq__(self, other):
        return isinstance(other, self.type)

    def __repr__(self):
        return '<instance of {!r}>'.format(self.type)


class iterable_with(object):
    """An object __eq__ to any iterable which yields `items`."""

    def __init__(self, items):
        self.items = items

    def __eq__(self, other):
        return list(other) == self.items

    def __repr__(self):
        return '<iterable with {!r}>'.format(self.items)


class mapping_containing(object):
    """An object __eq__ to any mapping with the passed `key`."""
    def __init__(self, key):
        self.key = key

    def __eq__(self, other):
        try:
            other[self.key]
        except (TypeError, KeyError):
            return False
        else:
            return True

    def __repr__(self):
        return '<mapping containing {!r}>'.format(self.key)
