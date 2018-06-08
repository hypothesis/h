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

By using the `InstanceOf` matcher you can simply write:

    foo.set_value.assert_called_once_with(matchers.InstanceOf(int))

As a bonus, the second test will print substantially more useful debugging
output if it fails, e.g.

    E       AssertionError: Expected call: set_value(<instance of <type 'int'>>)
    E       Actual call: set_value('a string')

"""
from __future__ import unicode_literals

import re

from pyramid import httpexceptions


class Matcher(object):
    def __eq__(self, other):
        raise NotImplementedError("subclasses should provide an __eq__ method")

    def __ne__(self, other):
        return not self.__eq__(other)


class AnyCallable(Matcher):
    """An object __eq__ to any callable object."""

    def __eq__(self, other):
        """Return ``True`` if ``other`` is callable, ``False`` otherwise."""
        return callable(other)


class NativeString(Matcher):
    """
    Matches any native string with the given characters.

    "Native string" means the ``str`` type which is a byte string in Python 2
    and a unicode string in Python 3. Does not match unicode strings (type
    ``unicode``) in Python 2, or byte strings (type ``bytes``) in Python 3,
    even if they contain the same characters.

    In Python 3 a ``bytes`` is never ``==`` to a ``str`` anyway, even if they
    contain the same characters. But in Python 2 a ``str`` is equal to a
    ``unicode`` if they contain the same characters, and that's why this
    matcher is needed.

    TODO: Delete this matcher once we no longer support Python 2.

    """

    def __init__(self, string):
        self.string = str(string)

    def __eq__(self, other):
        if not isinstance(other, str):
            return False
        return other == self.string

    def __repr__(self):
        return '<native string matching "{string}">'.format(string=self.string)

    def lower(self):
        return NativeString(self.string.lower())


class InstanceOf(Matcher):
    """An object __eq__ to any object which is an instance of `type_`."""

    def __init__(self, type_):
        self.type = type_

    def __eq__(self, other):
        return isinstance(other, self.type)

    def __repr__(self):
        return "<instance of {!r}>".format(self.type)


class IterableWith(Matcher):
    """An object __eq__ to any iterable which yields `items`."""

    def __init__(self, items):
        self.items = items

    def __eq__(self, other):
        return list(other) == self.items

    def __repr__(self):
        return "<iterable with {!r}>".format(self.items)


class MappingContaining(Matcher):
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
        return "<mapping containing {!r}>".format(self.key)


class Redirect302To(Matcher):
    """Matches any HTTPFound redirect to the given URL."""

    def __init__(self, location):
        self.location = location

    def __eq__(self, other):
        if not isinstance(other, httpexceptions.HTTPFound):
            return False
        return other.location == self.location


class Redirect303To(Matcher):
    """Matches any HTTPSeeOther redirect to the given URL."""

    def __init__(self, location):
        self.location = location

    def __eq__(self, other):
        if not isinstance(other, httpexceptions.HTTPSeeOther):
            return False
        return other.location == self.location


class Regex(Matcher):
    """Matches any string matching the passed regex."""

    def __init__(self, patt):
        self.patt = re.compile(patt)

    def __eq__(self, other):
        return bool(self.patt.match(other))

    def __repr__(self):
        return "<string matching re {!r}>".format(self.patt.pattern)


class UnorderedList(Matcher):
    """
    Matches a list with the same items in any order.

    Matches any list that contains the same items as the given list
    (and no more), regardless of order.

    """

    def __init__(self, items):
        self.items = items

    def __eq__(self, other):
        if len(self.items) != len(other):
            return False
        for item in self.items:
            if item not in other:
                return False
        return True

    def __repr__(self):
        return "<unordered list containing {items}".format(items=self.items)
